import logging
import socket
from .config import supabase
from .retry_utils import with_retries

def reset_agent_status():
    """Reset the agent's status to 'Checked-In' at startup."""
    hostname = socket.gethostname()

    def reset_status():
        # Use the supabase client directly
        supabase.table("settings").update({"check_in": "Checked-In"}).eq("hostname", hostname).execute()

    try:
        with_retries(reset_status)
    except Exception as e:
        logging.error(f"An error occurred while resetting agent status: {repr(e)}")

def update_settings_status(hostname, status):
    """Update the check-in status of the hostname in the settings table."""

    def update_status():
        supabase.table("settings").update({"check_in": status}).eq("hostname", hostname).execute()

    try:
        with_retries(update_status)
    except Exception as e:
        logging.error(f"An error occurred while updating status for {hostname}: {e}")