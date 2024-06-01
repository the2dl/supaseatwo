### `file_operations.py`
# File Operations Utility Functions

This module provides functions for handling file uploads and downloads, interacting with Supabase storage, and managing command statuses.

## Functions:
* `handle_download_command`: Handles the 'download' command by uploading the file to Supabase storage and updating the downloads table.
* `get_public_url`: Constructs the public URL for a file in Supabase storage.
* `update_command_status`: Updates the status of a command in the `py2` table.
* `download_from_supabase`: Downloads a file from Supabase storage and saves it locally.
* `fetch_pending_uploads`: Fetches pending uploads from the `uploads` table.
* `handle_upload_command`: Handles the 'upload' command by uploading the file to Supabase storage and updating the uploads table.