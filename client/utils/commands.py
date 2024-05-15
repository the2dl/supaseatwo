import time
import itertools
import os
import requests
import subprocess
import re

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
            print("  ps grep <pattern>                 :: Filter processes by name")
            print("  psrun <pattern>                   :: Start a new process via Powershell")
            print("  cmdrun <pattern>                  :: Start a new process via cmd")
            print("  kill                              :: Send a signal to terminate the agent")
            print("  wls <directory_path>              :: List contents of a directory on Windows host via Windows API")
            print("  wami                              :: Display user information on Windows host via Windows API")
            print("  users <group_name>                :: List users in the specified group on Windows host via Windows API")
            print("  smb write <local_file_path> <remote_smb_path> [username password domain]  :: Write a file to a remote host via SMB protocol")
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

        # Handle specific commands with arguments
        if command_text.startswith('ps grep'):
            try:
                _, _, pattern = command_text.split(maxsplit=2)
                command_text = f"powershell -Command \"Get-Process | Where-Object {{$_.ProcessName -like '*{pattern}*'}}\""
            except ValueError:
                print("Invalid ps grep command format. Use 'ps grep <pattern>'.")
                continue

        # psrun command
        if command_text.startswith("psrun "):
            try:
                _, command = command_text.split(maxsplit=1)
                subprocess.Popen(["powershell.exe", "-Command", f"Start-Process -FilePath '{command}'"])
                print(f"Started process: {command}")
                continue
            except ValueError:
                print("Invalid psrun command format. Use 'psrun <path_to_executable_or_file>'")
                continue

        # cmdrun command
        if command_text.startswith("cmdrun "):
            try:
                _, command = command_text.split(maxsplit=1)
                subprocess.Popen(["cmd.exe", "/c", f"start {command}"])  # Use "/c" to close cmd after
                print(f"Started process: {command}")
                continue
            except ValueError:
                print("Invalid cmdrun command format. Use 'cmdrun <path_to_executable_or_file>'")
                continue

        # Handle the new 'wls' command
        if command_text.startswith("wls"):
            parts = command_text.split(maxsplit=1)
            if len(parts) == 1:
                command_text = "wls ."  # Default to current directory if no path is provided
            else:
                command_text = f"wls {parts[1]}"

        # Handle the new 'wami' command
        if command_text == "wami":
            command_text = "wami"

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
        if command_text.startswith("smb write"):
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

        # Translate using command mappings
        command_text = command_mappings.get(command_text, command_text)

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

        first_pass = True
        while True:
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
                output = command_info.get('output', 'No output available')
                if command_info['status'] == 'Failed':
                    print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{hostname}{RESET}\n\n {output}")
                else:
                    print(f"\n\n{BLUE}Output:{RESET} from {GREEN}{hostname}{RESET}\n\n {output}")
                break  # Exit loop when command is done