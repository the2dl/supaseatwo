import time
import itertools
import readline
import os
import threading
from datetime import datetime, timedelta

# Import functions from the 'utils' package
from utils import login
from utils.commands import send_command_and_get_output
from utils.download import list_and_download_files
from utils.database import supabase

# Spinner for visual feedback
spinner = itertools.cycle(['|', '/', '-', '\\'])

# ANSI escape codes for colored output
GREEN = '\033[32m'
RED = '\033[31m'
BLUE = '\033[34m'
RESET = '\033[0m'

# Command mappings for shortcuts
command_mappings = {
    "psls": "powershell ls",
    "ps": "powershell get-process",
    "pspwd": "powershell pwd",
    "whoami": "whoami /all",
    # ... add more mappings as needed
}

# Default sleep interval and check-in threshold
current_sleep_interval = 5
CHECK_IN_THRESHOLD = timedelta(minutes=10)
DEFAULT_TIMEOUT = 600

def select_hostname():
    while True:  # Loop to ensure valid selection or allow repeated attempts
        # Fetch current data from the database
        response = supabase.table('settings').select('hostname, last_checked_in, check_in, timeout_interval').execute()
        hosts = response.data
        now = datetime.utcnow()

        if not hosts:
            print("No hosts found in the settings table.")
            return None  # Return None if no hosts are available

        print("\nList of Hosts:")
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

            color = RED if status in ["dead", "likely dead", "no check-in info"] else GREEN
            print(f"{index}. {color}{hostname} ({status}){RESET}")

        # Adding an exit option
        print(f"{len(hosts) + 1}. exit supaseatwo")

        try:
            choice = int(input("\nSelect a host to interact with or exit (by number). Hit enter to refresh availability: "))
            if 1 <= choice <= len(hosts):
                selected_host = hosts[choice - 1]['hostname']
                print(f"You have selected {selected_host}.")
                return selected_host  # Successfully return the selected hostname
            elif choice == len(hosts) + 1:
                print("byebye.")
                return None  # User chooses to exit
            else:
                print("Invalid selection. Please enter a number within the list range.")
        except ValueError:
            print("Invalid selection. Please enter a valid number.")


def get_host_status(hostname):
    """Fetch the current status of the host from the database."""
    response = supabase.table('settings').select('check_in').eq('hostname', hostname).execute()
    if response.data:
        return response.data[0]['check_in']
    return 'Unknown'

def main():
    username = login.login()
    if username is None:
        print("Login failed or was cancelled.")
        return

    hostname = select_hostname()

    while hostname:
        print(f"\nInteracting with '{GREEN}{hostname}{RESET}' with user '{username}'\n")
        print("1. Interact")
        print("2. Exit to Host Selection")
        print("3. Exit to Local Terminal")
        print("4. List Downloads")

        choice = input("\nEnter your choice: ")
        try:
            choice = int(choice)
            if choice == 1:
                send_command_and_get_output(hostname, username, command_mappings, current_sleep_interval)
            elif choice == 2:
                hostname = select_hostname()
            elif choice == 3:
                break
            elif choice == 4:
                list_and_download_files(hostname)
            else:
                print("Invalid choice. Please try again.")

            # After processing the command, check the status of the host
            host_status = get_host_status(hostname)
            if host_status in ['dead', 'likely dead']:
                print(f"Host {hostname} is {host_status}. Selecting a new host.")
                hostname = select_hostname()  # Prompt to select a new host
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
