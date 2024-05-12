import time
import itertools
import readline
import os
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

def select_hostname():
    response = supabase.table('settings').select('hostname', 'last_checked_in').execute()
    hosts = response.data
    now = datetime.utcnow()
    if not hosts:
        print("No hosts found in the settings table.")
        return None

    print("\nList of Hosts:")
    for index, host in enumerate(hosts, start=1):
        last_checked_in_str = host.get('last_checked_in')
        if last_checked_in_str:
            last_checked_in = datetime.fromisoformat(last_checked_in_str[:-1])
            time_difference = now - last_checked_in
            if time_difference > CHECK_IN_THRESHOLD:
                color = RED
                status = "likely dead"
            else:
                color = GREEN
                status = "alive"
        else:
            color = RED
            status = "likely dead"
        print(f"{index}. {color}{host['hostname']} ({status}){RESET}")

    try:
        choice = int(input("\nSelect a host to interact with (by number): "))
        selected_host = hosts[choice - 1]['hostname']
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None
    return selected_host

def main():
    username = login.login()
    if username is None:
        return

    hostname = select_hostname()
    while hostname:
        print(f"\nInteracting with '{GREEN}{hostname}{RESET}' with user '{username}'\n")
        print("1. Interact")
        print("2. Exit to Host Selection")
        print("3. Exit to Local Terminal")
        print("4. List Downloads")
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid choice. Please enter a number.")
            continue
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

if __name__ == "__main__":
    main()
