import os
import win32file
from datetime import datetime

def get_file_attributes_string(file_attributes):
    """Convert file attributes to a string representing the mode."""
    attributes = [
        ('d', win32file.FILE_ATTRIBUTE_DIRECTORY),
        ('r', win32file.FILE_ATTRIBUTE_READONLY),
        ('h', win32file.FILE_ATTRIBUTE_HIDDEN),
        ('s', win32file.FILE_ATTRIBUTE_SYSTEM),
        ('a', win32file.FILE_ATTRIBUTE_ARCHIVE)
    ]
    mode = ''.join(attr if (file_attributes & flag) else '-' for attr, flag in attributes)
    return mode

def format_file_info(file_info):
    """Format file information into a readable string."""
    mode = get_file_attributes_string(file_info[0])
    last_write_time = file_info[3]  # This is already a pywintypes.datetime object
    if last_write_time:
        last_write_time_str = last_write_time.strftime('%m/%d/%Y %I:%M %p')
    else:
        last_write_time_str = 'Unknown'

    length = file_info[5] if mode[0] != 'd' else 0  # Directories have a length of 0
    name = file_info[8]
    return f"{mode:<10} {last_write_time_str:<22} {length:<12} {name}"

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