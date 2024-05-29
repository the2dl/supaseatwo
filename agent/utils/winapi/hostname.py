# hostname.py

import socket

def get_hostname():
    """Retrieves the local hostname using the socket library."""
    try:
        hostname = socket.gethostname()
        return f"Hostname: {hostname}"
    except Exception as e:
        return f"Error: {str(e)}"
