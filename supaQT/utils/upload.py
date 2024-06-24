import os
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
from utils.database import db_manager, get_public_url

class Uploader(QObject):
    upload_progress = pyqtSignal(str)
    upload_complete = pyqtSignal(str, str)  # Emits filename and remote URL
    upload_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def upload_file(self, agent_id, hostname, local_path, remote_path, username):
        """Uploads a file to the specified host via Supabase storage."""

        bucket_name = "files"  # Name of the storage bucket in Supabase
        try:
            # Check if the local file exists
            if not os.path.exists(local_path):
                self.upload_error.emit(f"Error: Local file '{local_path}' not found.")
                return

            if os.path.isdir(local_path):
                self.upload_error.emit(f"Error: Invalid path, it is a directory: {local_path}")
                return

            filename = os.path.basename(local_path)
            storage_path = f"uploads/{filename}"

            self.upload_progress.emit(f"Uploading '{local_path}' as '{storage_path}' on '{hostname}'...")

            # Open the file in binary mode and upload to Supabase
            with open(local_path, 'rb') as f:
                response = db_manager.upload_file(bucket_name, storage_path, f)

                # Check if the upload was successful
                if response.status_code not in [200, 201]:
                    raise Exception(f"Failed to upload: {response.json().get('message')}")

            # Get the public URL for the uploaded file
            file_url = get_public_url(bucket_name, storage_path)
            self.upload_progress.emit(f"Upload successful! File available at: {file_url}")

            # Store upload information in the database
            db_manager.insert_upload({
                'agent_id': agent_id,
                'hostname': hostname,
                'local_path': local_path,
                'remote_path': remote_path,
                'file_url': file_url,
                'username': username,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'Completed'
            })

            self.upload_complete.emit(filename, file_url)
            return "Completed", f"File uploaded to {file_url}"

        except Exception as e:
            error_message = f"Upload failed: {e}"
            self.upload_error.emit(error_message)
            return "Failed", error_message

uploader = Uploader()

def upload_file(agent_id, hostname, local_path, remote_path, username):
    """Function to be called from other parts of the application."""
    return uploader.upload_file(agent_id, hostname, local_path, remote_path, username)
