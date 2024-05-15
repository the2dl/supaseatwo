from datetime import datetime
from .get_file_attributes_string import get_file_attributes_string

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
