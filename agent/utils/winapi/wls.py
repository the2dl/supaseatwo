import os
import win32file
from .format_file_info import format_file_info

def wls(path):
    """Lists all files and directories at the given path using Windows native APIs."""
    files = ["Permissions  Last Write Time       Size       Name"]
    files.append("-----------  -------------------  ---------- ----------------------------------")
    try:
        # Normalize the path to ensure compatibility with FindFilesW
        normalized_path = os.path.normpath(path)
        if not os.path.isdir(normalized_path):
            raise ValueError(f"The path '{normalized_path}' is not a valid directory.")

        # Ensure path is a directory
        handle = win32file.FindFilesW(normalized_path + '\\*')

        for file in handle:
            files.append(format_file_info(file))
    except Exception as e:
        files = ["Error: " + str(e)]

    return files
