import logging
import socket
from .config import supabase

def reset_agent_status(supabase):
    """Reset the agent's status to 'Checked-In' at startup."""
    hostname = socket.gethostname()
    try:
        # Use the supabase client directly
        supabase.table("settings").update({"check_in": "Checked-In"}).eq("hostname", hostname).execute()
    except Exception as e:
        logging.error(f"An error occurred while resetting agent status: {repr(e)}")


def update_settings_status(supabase, hostname, status):
    """Update the check-in status of the hostname in the settings table."""
    try:
        supabase.table("settings").update({"check_in": status}).eq("hostname", hostname).execute()
    except Exception as e:
        logging.error(f"An error occurred while updating status for {hostname}: {e}")