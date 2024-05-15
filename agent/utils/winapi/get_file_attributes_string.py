import win32file

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
