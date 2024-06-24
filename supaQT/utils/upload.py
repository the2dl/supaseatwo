import os
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
from utils.database import db_manager, get_public_url, supabase

class Uploader(QObject):
    upload_progress = pyqtSignal(str)
    upload_complete = pyqtSignal(str, str)  # We'll emit filename and target path
    upload_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def upload_file(self, agent_id, hostname, local_path, remote_path, username):
        bucket_name = "files"
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file '{local_path}' not found.")

            if os.path.isdir(local_path):
                raise IsADirectoryError(f"Invalid path, it is a directory: {local_path}")

            filename = os.path.basename(local_path)
            storage_path = f"uploads/{filename}"

            self.upload_progress.emit(f"Uploading '{local_path}' as '{storage_path}' on '{hostname}'...")

            with open(local_path, 'rb') as f:
                response = supabase.storage.from_(bucket_name).upload(storage_path, f)

                if response.status_code not in [200, 201]:
                    raise Exception(f"Failed to upload: {response.json().get('message')}")

            file_url = get_public_url(bucket_name, storage_path)

            supabase.table("uploads").insert({
                'agent_id': agent_id,
                'hostname': hostname,
                'local_path': local_path,
                'remote_path': remote_path,
                'file_url': file_url,
                'username': username,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'pending'
            }).execute()

            self.upload_complete.emit(filename, remote_path)
            return "Completed", f"File uploaded successfully"

        except Exception as e:
            error_message = f"Upload failed: {str(e)}"
            self.upload_error.emit(error_message)
            return "Failed", error_message

uploader = Uploader()

def upload_file(agent_id, hostname, local_path, remote_path, username):
    return uploader.upload_file(agent_id, hostname, local_path, remote_path, username)