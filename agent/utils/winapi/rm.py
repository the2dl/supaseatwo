# utils/winapi/rm.py

import os
import shutil

def rm(path):
    """Deletes a file or directory at the given path using Windows native APIs."""
    try:
        if not path:
            raise ValueError("Path cannot be empty.")

        normalized_path = os.path.normpath(path)

        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"The path '{normalized_path}' does not exist.")

        if os.path.isdir(normalized_path):
            shutil.rmtree(normalized_path)
        else:
            os.remove(normalized_path)

        return f"Deleted '{normalized_path}'."
    except Exception as e:
        return f"Error deleting file or directory: {str(e)}"
