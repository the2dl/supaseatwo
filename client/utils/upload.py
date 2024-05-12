import os
import requests
from datetime import datetime  # Import datetime module

from .database import supabase, get_public_url

def upload_file(hostname, local_path, remote_path, username):
    """Uploads a file to the specified host via Supabase storage."""

    bucket_name = "files"  # Name of the storage bucket in Supabase
    try:
        # Check if the local file exists
        if not os.path.exists(local_path):
            print(f"Error: Local file '{local_path}' not found.")
            return

        filename = os.path.basename(local_path)  # Extract filename
        storage_path = f"uploads/{filename}"    # Path within the bucket

        print(f"Uploading '{local_path}' as '{storage_path}' on '{hostname}'...")

        # Open the file in binary mode and upload to Supabase
        with open(local_path, 'rb') as f:
            response = supabase.storage.from_(bucket_name).upload(storage_path, f)

            # Check if the upload was successful
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to upload: {response.json().get('message')}")

        # Get the public URL for the uploaded file
        file_url = get_public_url(bucket_name, storage_path)
        print(f"Upload successful! File available at: {file_url}")

        # Store upload information in the database
        supabase.table("uploads").insert({
            'hostname': hostname,
            'local_path': local_path,
            'remote_path': remote_path,   # Store the full path for downloading
            'file_url': file_url,
            'username': username,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'  # Initially set status as pending
        }).execute()

    except Exception as e:
        print(f"Upload failed: {e}")
