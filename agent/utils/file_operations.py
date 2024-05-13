import os
import mimetypes
import requests
import supabase
from supabase import Client
from .config import SUPABASE_URL, SUPABASE_KEY, bucket_name
from .system_info import get_system_info # import get_system_info function from system_info.py

def handle_download_command(command_text, username, supabase):
    """Handle the 'download' command by uploading the file to Supabase storage and updating the downloads table."""
    try:
        _, file_path = command_text.split(maxsplit=1)

        # Input validation for the file path
        if not os.path.exists(file_path):
            return "Failed", f"File does not exist: {file_path}"

        if os.path.isdir(file_path):
            return "Failed", f"Invalid path, it is a directory: {file_path}"

        # Determine the mimetype of the file
        mimetype, _ = mimetypes.guess_type(file_path)
        mimetype = mimetype if mimetype else "application/octet-stream"
        file_name = os.path.basename(file_path)
        storage_path = f"downloads/{file_name}"

        # Upload the file to Supabase storage
        with open(file_path, "rb") as f:
            response = supabase.storage.from_(bucket_name).upload(storage_path, f, file_options={"content_type": mimetype})

        if response.status_code in [200, 201]:
            # Construct the public URL for the uploaded file
            file_url = get_public_url(bucket_name, storage_path)

            # Insert download record into the database
            hostname, _, _ = get_system_info()
            supabase.table("downloads").insert({
                "hostname": hostname,
                "local_path": file_path,
                "remote_path": storage_path,
                "file_url": file_url,
                "username": username,
                "status": "Completed"
            }).execute()
            return "Completed", f"File uploaded and available at {file_url}"

        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return "Failed", f"Upload failed: {error_message}"
    except Exception as e:
        return "Failed", f"An unexpected error occurred: {str(e)}"

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"

def download_from_supabase(file_url, remote_path, supabase_key, supabase):
    """Downloads a file from Supabase storage and uploads it to your bucket."""

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }

    local_directory = os.path.dirname(remote_path)
    if local_directory and not os.path.exists(local_directory):
        os.makedirs(local_directory, exist_ok=True)

    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        with open(remote_path, "wb") as file:
            file.write(response.content)

        supabase.storage.from_(bucket_name).upload(
            remote_path, remote_path, file_options={"content_type": mimetypes.guess_type(remote_path)[0]}
        )

        return True
    else:
        return False

def fetch_pending_uploads(supabase: Client):  # Add supabase client as argument
    """Fetches pending uploads from the 'uploads' table."""
    response = supabase.table("uploads").select("*").eq("status", "pending").execute()
    return response

def handle_upload_command(command_text, output_path, username):
    """Handle the 'upload' command by uploading the file to Supabase storage and updating the uploads table."""
    try:
        _, local_path, remote_path = command_text.split(maxsplit=2)

        if not os.path.exists(local_path):
            return "Failed", f"File does not exist: {local_path}"

        if os.path.isdir(local_path):
            return "Failed", f"Invalid path, it is a directory: {local_path}"

        # Get the mime type of the file for correct handling in storage
        mimetype, _ = mimetypes.guess_type(local_path)

        with open(local_path, "rb") as f:
            response = supabase.storage.from_(bucket_name).upload(remote_path, f, file_options={"content_type": mimetype})

        if response.status_code in [200, 201]:
            # Construct public URL for the uploaded file
            file_url = get_public_url(bucket_name, remote_path)
            # Update the uploads table
            supabase.table("uploads").insert({
                "local_path": local_path,
                "remote_path": remote_path,
                "file_url": file_url,
                "username": username,
                "status": "pending"  # You might want to change the status later
            }).execute()
            return "Completed", f"File uploaded to {file_url}"
        else:
            return "Failed", f"Upload failed with status code: {response.status_code}"

    except Exception as e:
        return "Failed", f"An unexpected error occurred: {str(e)}"