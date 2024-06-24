import os
import requests
import time
from PyQt5.QtCore import QObject, pyqtSignal
from .database import db_manager, get_public_url
from .encryption_utils import encryption_manager

class Downloader(QObject):
    download_progress = pyqtSignal(str)
    download_complete = pyqtSignal(str, str)  # Emits filename and local path
    download_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def sanitize_path(self, file_path):
        """Sanitize the file path to ensure it is correctly formatted for the remote path."""
        return file_path.replace("\\", "/").split(":/")[-1]

    def download_file(self, agent_id, hostname, file_path, username):
        """Triggers the download process on the remote machine and stores the file in Supabase storage."""

        sanitized_path = self.sanitize_path(file_path)
        filename = os.path.basename(sanitized_path)

        # Insert a new record into the downloads table
        result = db_manager.insert_download({
            'agent_id': agent_id,
            'hostname': hostname,
            'local_path': file_path,
            'remote_path': f"downloads/{filename}",
            'file_url': '',
            'username': username,
            'status': 'Pending'
        })

        command_id = result.data[0]['id']
        self.download_progress.emit(f"Download command '{file_path}' added with ID {command_id}.")

        # Poll for download completion
        while True:
            db_response = db_manager.get_download_status(command_id)
            command_info = db_response.data[0]

            if command_info['status'] == 'Completed':
                file_url = command_info.get('file_url', '')
                if file_url.startswith('http'):
                    self.download_progress.emit(f"File available at URL: {file_url}")
                    self.download_complete.emit(filename, file_url)
                else:
                    self.download_error.emit(f"Download failed: Invalid URL '{file_url}'")
                break

            elif command_info['status'] == 'Failed':
                output_text = command_info.get('output', '')
                self.download_error.emit(f"Error: {output_text}")
                break

            time.sleep(5)

    def download_file_from_supabase(self, file_url, local_path):
        """Downloads a file directly from Supabase storage."""
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path) or '.'
            os.makedirs(local_dir, exist_ok=True)

            # Download file using the public URL
            response = requests.get(file_url, headers=db_manager.get_auth_headers())
            response.raise_for_status()

            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            self.download_progress.emit(f"File downloaded to {local_path}")
            self.download_complete.emit(os.path.basename(local_path), local_path)
        except requests.exceptions.RequestException as e:
            self.download_error.emit(f"Download failed: {e}")
        except OSError as e:
            self.download_error.emit(f"Invalid directory: {e}")

    def list_downloads(self, hostname):
        """List completed downloads for a specific hostname."""
        downloads = db_manager.get_completed_downloads(hostname)
        return downloads

downloader = Downloader()

def download_file(agent_id, hostname, file_path, username):
    """Function to be called from other parts of the application."""
    downloader.download_file(agent_id, hostname, file_path, username)

def list_and_download_files(hostname):
    """List and download files for a specific hostname based on the downloads table."""
    downloads = downloader.list_downloads(hostname)
    
    if not downloads:
        return "No completed downloads found for this host."

    output = ["Available Downloads:"]
    for i, download in enumerate(downloads, 1):
        output.append(f"{i}. {download['local_path']} at {download['remote_path']} (URL: {download['file_url']})")

    return "\n".join(output)

def download_selected_file(hostname, index, local_path):
    """Download a selected file from the list of available downloads."""
    downloads = downloader.list_downloads(hostname)
    
    if 0 < index <= len(downloads):
        selected_download = downloads[index - 1]
        file_name = os.path.basename(selected_download['remote_path'])
        
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, file_name)
        
        downloader.download_file_from_supabase(selected_download['file_url'], local_path)
        return f"Downloading '{file_name}' to '{local_path}'..."
    else:
        return "Invalid selection. Please try again."
