import socket
import platform

def get_system_info():
    """Retrieve the hostname, IP address, and OS of the current system."""
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except socket.error:
        ip = "Unavailable"
    os_info = platform.system() + " " + platform.release()
    return hostname, ip, os_info