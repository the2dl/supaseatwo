import time
from PyQt5.QtCore import QObject, pyqtSignal
from utils.database import supabase, db_manager
from utils.encryption_utils import encrypt_response, decrypt_output, encryption_manager
from datetime import datetime
from utils.ai_summary import generate_summary

class CommandExecutor(QObject):
    command_output = pyqtSignal(str)
    command_completed = pyqtSignal(str, str, str)  # command, output, summary

    def __init__(self):
        super().__init__()

    def execute_command(self, hostname, username, command, encryption_key):
        agent_id, _ = encryption_manager.fetch_agent_info_by_hostname(hostname)
        if not agent_id:
            self.command_output.emit(f"Error: Unable to find agent_id for hostname {hostname}.")
            return None, None  # Return None, None instead of just returning

        encrypted_command = encryption_manager.encrypt(command, encryption_key)

        result = db_manager.insert_command(agent_id, hostname, username, encrypted_command)

        if not result.data:
            self.command_output.emit(f"Error: Failed to insert command for {hostname}")
            return None, None  # Return None, None instead of just returning

        command_id = result.data[0]['id']
        self.command_output.emit(f"Command added with ID {command_id}. Waiting for execution...")

        while True:
            status = db_manager.get_command_status(command_id)
            if status.data[0]['status'] in ['Completed', 'Failed']:
                encrypted_output = status.data[0]['output']
                decrypted_output = encryption_manager.decrypt(encrypted_output, encryption_key)
                
                # Generate AI summary
                summary = generate_summary(command, decrypted_output)
                
                # Encrypt the summary
                encrypted_summary = encryption_manager.encrypt(summary, encryption_key)
                
                # Update the Supabase database with the encrypted AI summary
                db_manager.update_command_summary(command_id, encrypted_summary)
                
                self.command_completed.emit(command, decrypted_output, summary)
                break

    def get_agent_info(self, hostname):
        response = supabase.table('settings').select('agent_id', 'encryption_key').eq('hostname', hostname).execute()
        if response.data:
            agent_info = response.data[0]
            encryption_key = agent_info.get('encryption_key')
            if encryption_key:
                encryption_key = encryption_key.encode()
            return agent_info['agent_id'], encryption_key
        return None, None

    def set_sleep_interval(self, interval):
        self.current_sleep_interval = interval