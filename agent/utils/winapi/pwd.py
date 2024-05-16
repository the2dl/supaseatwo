import os

def wpwd():
    """Returns the current working directory of the local machine."""
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error: {str(e)}"
