# nslookup.py

import socket

def nslookup(hostname):
    """Performs a DNS lookup for the given hostname using the socket library."""
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        results = []
        for info in addr_info:
            results.append(f"Address: {info[4][0]}")
        return "\n".join(results)
    except socket.gaierror as e:
        return f"Error: {str(e)}"
