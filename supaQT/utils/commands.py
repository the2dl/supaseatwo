import time
import itertools
import os
import threading
import shlex
from cryptography.fernet import Fernet
import logging

from utils.database import supabase, get_public_url
from utils.download import download_file
from utils.upload import upload_file
from utils.ai_summary import generate_summary
from utils.encryption_utils import fetch_agent_info_by_hostname, encrypt_response, decrypt_output
from utils.help import display_detailed_help, display_help, detailed_help

class CommandHandler:
    def __init__(self):
        self.GREEN = '\033[32m'
        self.RED = '\033[31m'
        self.BLUE = '\033[34m'
        self.PURPLE = '\033[35m'
        self.LIGHT_GREY = '\033[38;5;250m'
        self.YELLOW = '\033[33m'
        self.RESET = '\033[0m'
        self.LIGHT_CYAN = '\033[96m'

        self.AI_SUMMARY = True
        self.current_sleep_interval = 5

    def execute_command(self, hostname, username, command_text, encryption_key):
        agent_id, _ = fetch_agent_info_by_hostname(hostname)
        if not agent_id:
            return f"{self.RED}Error:{self.RESET} Unable to find agent_id for hostname {hostname}."

        if command_text.startswith("download"):
            return self.handle_download(agent_id, hostname, command_text, username)

        if command_text.startswith("upload"):
            return self.handle_upload(agent_id, hostname, command_text, username)

        if command_text == "view_history":
            return self.view_command_history(hostname)

        if command_text.startswith("view_history grep"):
            parts = command_text.split(maxsplit=2)
            if len(parts) == 3:
                return self.view_command_history(hostname, parts[2])
            else:
                return f"{self.RED}Error:{self.RESET} Invalid view_history command format. Use 'view_history grep <search_term>'."

        encrypted_command = encrypt_response(command_text, encryption_key)

        result = supabase.table('py2').insert({
            'agent_id': agent_id,
            'hostname': hostname,
            'username': username,
            'command': encrypted_command,
            'status': 'Pending'
        }).execute()

        command_id = result.data[0]['id']
        output = [f"Command '{command_text}' added with ID {command_id}.", "Waiting for the command to complete..."]

        completed_event = threading.Event()
        printed_flag = threading.Event()
        
        def background_check():
            while not completed_event.is_set():
                time.sleep(self.current_sleep_interval)
                response = supabase.table('py2').select('status', 'command', 'output', 'smbhost').eq('id', command_id).execute()
                command_info = response.data[0]

                if command_info['status'] in ('Completed', 'Failed'):
                    smbhost = command_info.get('smbhost')
                    output_text = command_info.get('output', 'No output available')
                    cmd = command_info.get('command', 'No command available')

                    try:
                        decrypted_output = decrypt_output(output_text, encryption_key)
                        decrypted_cmd = decrypt_output(cmd, encryption_key)
                    except Exception as e:
                        output.append(f"{self.RED}Error:{self.RESET} Failed to decrypt output: {e}")
                        decrypted_output = "Failed to decrypt output."
                        decrypted_cmd = command_text

                    display_hostname = smbhost if smbhost else hostname
                    if command_info['status'] == 'Failed':
                        output.append(f"\n\n{self.RED}Error:{self.RESET} Command failed on {self.GREEN}{display_hostname}{self.RESET}\n\n {decrypted_output}")
                    else:
                        output.append(f"\n\nOutput from {self.GREEN}{display_hostname}{self.RESET}\n\n {decrypted_output}\n")

                    if self.AI_SUMMARY:
                        ai_summary = generate_summary(decrypted_cmd, decrypted_output)
                        if ai_summary:
                            encrypted_summary = encrypt_response(ai_summary, encryption_key)
                            output.append(f"\n{self.BLUE}AI Summary:{self.RESET} {ai_summary}\n")
                            supabase.table('py2').update({'ai_summary': encrypted_summary}).eq('id', command_id).execute()

                    completed_event.set()
                    break

        threading.Thread(target=background_check, daemon=True).start()

        completed_event.wait(timeout=600)  # Wait for up to 10 minutes

        if not completed_event.is_set():
            output.append(f"\n{self.RED}Error:{self.RESET} Command timeout. No response from {hostname} for 10 minutes.")

        return "\n".join(output)

    def handle_download(self, agent_id, hostname, command_text, username):
        parts = command_text.split(maxsplit=1)
        if len(parts) < 2:
            return f"{self.RED}Error:{self.RESET} Invalid download command format. Use 'download <file_path>'."
        
        _, file_path = parts
        return download_file(agent_id, hostname, file_path, username)

    def handle_upload(self, agent_id, hostname, command_text, username):
        parts = command_text.split(maxsplit=2)
        if len(parts) != 3:
            return f"{self.RED}Error:{self.RESET} Invalid upload command format. Use 'upload <local_path> <remote_path>'."
        
        _, local_path, remote_path = parts
        return upload_file(agent_id, hostname, local_path, remote_path, username)

    def view_command_history(self, hostname, search_term=None):
        response = supabase.table('py2').select(
            'created_at', 'hostname', 'username', 'ip', 'command', 'output', 'smbhost', 'ai_summary'
        ).or_(
            f"hostname.eq.{hostname},smbhost.eq.{hostname}"
        ).execute()

        commands = response.data
        if not commands:
            return f"\n{self.YELLOW}No command history available for {hostname}.{self.RESET}"

        _, encryption_key = fetch_agent_info_by_hostname(hostname)

        output = []
        for command in commands:
            if encryption_key:
                try:
                    command['output'] = decrypt_output(command['output'], encryption_key)
                    command['command'] = decrypt_output(command['command'], encryption_key)
                    if command['ai_summary']:
                        command['ai_summary'] = decrypt_output(command['ai_summary'], encryption_key)
                except Exception as e:
                    output.append(f"{self.RED}Error:{self.RESET} Failed to decrypt output: {e}")

        if search_term:
            commands = [cmd for cmd in commands if search_term.lower() in (cmd.get('output', '')).lower()]

        if not commands:
            return f"\n{self.YELLOW}No matches found for the search term '{search_term}' in command history for {hostname}.{self.RESET}"

        output.append(f"\n{self.GREEN}Command History for {hostname}:{self.RESET}")

        for command in commands:
            created_at = command['created_at']
            username = command['username']
            ip = command.get('ip', 'N/A')
            cmd = command['command']
            cmd_output = command['output']
            ai_summary = command.get('ai_summary', 'No summary available')

            if command.get('smbhost'):
                exec_hostname = command['smbhost']
                color = self.RED
            else:
                exec_hostname = command['hostname']
                color = self.RESET

            output.extend([
                f"\n{color}Time:{self.RESET} {created_at}",
                f"{color}User:{self.RESET} {username}",
                f"{color}IP:{self.RESET} {ip}",
                f"{color}Hostname:{self.RESET} {exec_hostname}",
                f"{color}Command:{self.RESET} {cmd}",
                f"{color}Output:{self.RESET} {cmd_output}",
                f"{color}AI Summary:{self.RESET} {ai_summary}",
                f"{self.PURPLE}{'-' * 50}{self.RESET}"
            ])

        return "\n".join(output)

    def set_sleep_interval(self, interval):
        self.current_sleep_interval = interval

    def toggle_ai_summary(self):
        self.AI_SUMMARY = not self.AI_SUMMARY
        return f"AI summary is now {'enabled' if self.AI_SUMMARY else 'disabled'}."

command_handler = CommandHandler()
