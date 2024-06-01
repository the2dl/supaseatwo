# utils/winapi/cd.py

import os

def cd(directory):
    """Changes the current working directory to the specified directory."""
    try:
        os.chdir(directory)
        return f"Directory changed to {os.getcwd()}"
    except Exception as e:
        return f"Error: {str(e)}"
