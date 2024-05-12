import os
import requests

from .database import supabase, get_public_url, SUPABASE_KEY

def download_file(hostname, file_path, username):
    """Downloads a file from the specified host."""

    # Insert a new record into the py2 table in Supabase to trigger the download process
    # on the remote machine.
    result = supabase.table('py2').insert({
        'hostname': hostname,
        'username': username,
        'command': f'download {file_path}',
        'status': 'Pending'
    }).execute()

    command_id = result.data[0]['id']
    print(f"Download command '{file_path}' added with ID {command_id}.")

    # Repeatedly poll Supabase to check if the download has completed
    while True:
        db_response = supabase.table('py2').select('status', 'output').eq('id', command_id).execute()
        command_info = db_response.data[0]  # Assuming only one record matches

        if command_info['status'] == 'Completed':
            output_text = command_info['output']
            if 'available at' in output_text:
                file_url = output_text.split('available at ')[1].strip()  # Extract URL part after 'available at '
                if file_url.startswith('http'):  # Check if valid URL
                    try:
                        print(f"Trying to download from URL: {file_url}")  # Debug print

                        # Headers for authenticated Supabase request
                        headers = {
                            'apikey': SUPABASE_KEY,
                            'Authorization': f'Bearer {SUPABASE_KEY}'
                        }

                        response = requests.get(file_url, headers=headers)
                        response.raise_for_status()  # Raise error for bad responses (4xx or 5xx)

                        # Create local directory if it doesn't exist
                        local_dir = os.path.dirname(file_path)
                        if not os.path.exists(local_dir):
                            os.makedirs(local_dir)

                        # Write downloaded content to file
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print(f"File '{file_path}' downloaded successfully.")
                        break
                    except requests.exceptions.RequestException as e:  # Handle download errors
                        print(f"Download failed: {e}")
                else:
                    print(f"Download failed: Invalid URL '{file_url}'")
            else:
                print("Error: Unexpected output format.")
            break  # Exit the loop after handling the command

def download_file_from_supabase(file_url, local_path):
    """Downloads a file directly from Supabase storage."""
    try:
        # Create local directory if it doesn't exist
        local_dir = os.path.dirname(local_path) or '.'
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        # Download file using the public URL
        headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()

        # Write to local file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully to {local_path}")
    except requests.exceptions.RequestException as e:
        print(f"Download failed: {response.status_code} - {response.reason} - {e}")
    except OSError as e:
        print(f"Invalid directory: {e}")

def list_and_download_files(hostname):
    """List and download files for a specific hostname based on the downloads table."""
    print(f"Fetching download records for {hostname}...")
    downloads = supabase.table("downloads").select("*").eq("hostname", hostname).eq("status", "Completed").execute().data

    if not downloads:
        print("No completed downloads found for this host.")
        return

    print("\nAvailable Downloads:")
    for i, download in enumerate(downloads, 1):
        print(f"{i}. {download['local_path']} at {download['remote_path']} (URL: {download['file_url']})")

    try:
        choice = int(input("\nEnter the number of the file to download (or 0 to go back): "))
        if choice == 0:
            return
        elif 0 < choice <= len(downloads):
            selected_download = downloads[choice - 1]
            file_name = os.path.basename(selected_download['remote_path'])
            file_path = input(f"Enter the local path to save (ex. /home/user/file.txt) '{file_name}': ")
            if os.path.isdir(file_path) or not os.path.exists(os.path.dirname(file_path) or '.'):
                print("Invalid directory. Please enter a valid directory path.")
                return

            print(f"Downloading '{file_name}' to '{file_path}'...")
            download_file_from_supabase(selected_download['file_url'], file_path)
        else:
            print("Invalid choice. Please try again.")
    except ValueError:
        print("Please enter a valid number.")
    except FileNotFoundError as e:
        print(f"Invalid directory: {e}")