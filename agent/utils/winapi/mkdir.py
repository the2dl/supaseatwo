# utils/winapi/mkdir.py

import os
import win32file

def mkdir(path):
    """Creates a directory at the given path using Windows native APIs."""
    try:
        if not path:
            raise ValueError("Path cannot be empty.")

        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path):
            raise FileExistsError(f"The directory '{normalized_path}' already exists.")

        win32file.CreateDirectory(normalized_path, None)
        return f"Directory '{normalized_path}' created successfully."
    except Exception as e:
        return f"Error creating directory: {str(e)}"
