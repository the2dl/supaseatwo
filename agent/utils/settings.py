import logging
import httpx
import os
from datetime import datetime
from cryptography.fernet import Fernet
from .system_info import get_system_info
from .config import supabase, DEFAULT_TIMEOUT, DEFAULT_CHECK_IN
from .retry_utils import with_retries

# Suppress logs from httpx and supabase-py
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)

logging.basicConfig(level=logging.WARNING)

def get_external_ip():
    """Get the external IP address of the agent by querying ipinfo.io."""
    try:
        response = with_retries(lambda: httpx.get('https://ipinfo.io'))
        if response.status_code == 200:
            ip_info = response.json()
            return ip_info.get('ip')
        else:
            logging.error(f"Failed to get external IP, status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"An error occurred while getting the external IP address: {repr(e)}")
        return None

def fetch_agent_id_by_hostname(hostname):
    """Fetch the agent_id using the hostname."""
    response = with_retries(lambda: supabase.table('settings').select('agent_id').eq('hostname', hostname).limit(1).execute())
    data = response.data
    if data:
        return data[0]['agent_id']
    return None

def fetch_settings(agent_id):
    """Fetch the system settings from the settings table, or return default values."""
    hostname, ip, os_info = get_system_info()
    local_user = os.getlogin()  # Fetch the current user's username
    response = with_retries(lambda: supabase.table('settings').select('*').eq('agent_id', agent_id).limit(1).execute())
    settings_data = response.data

    now = datetime.utcnow().isoformat() + "Z"  # Timestamp in UTC format

    if settings_data:
        settings = settings_data[0]
        timeout_interval = settings.get('timeout_interval', DEFAULT_TIMEOUT)
        check_in_status = settings.get('check_in', DEFAULT_CHECK_IN)
        external_ip = settings.get('external_ip')
        encryption_key = settings.get('encryption_key')

        # Fetch external IP if not already stored
        if not external_ip:
            external_ip = get_external_ip()
            if external_ip:
                try:
                    with_retries(lambda: supabase.table('settings').update({
                        'external_ip': external_ip
                    }).eq('agent_id', agent_id).execute())
                except Exception as e:
                    logging.warning(f"Failed to update external IP: {e}")

        # Generate and store encryption key if not already stored
        if not encryption_key:
            encryption_key = Fernet.generate_key().decode()
            logging.debug(f"Generated encryption key: {encryption_key}")
            try:
                with_retries(lambda: supabase.table('settings').update({
                    'encryption_key': encryption_key
                }).eq('agent_id', agent_id).execute())
            except Exception as e:
                logging.warning(f"Failed to update encryption key: {e}")
        else:
            logging.debug(f"Fetched existing encryption key: {encryption_key}")

        # Update the last checked-in time and localuser with error handling
        try:
            with_retries(lambda: supabase.table('settings').update({
                'last_checked_in': now,
                'localuser': local_user
            }).eq('agent_id', agent_id).execute())
        except Exception as e:
            logging.warning(f"Failed to update last checked-in time and localuser: {e}")

        return timeout_interval, check_in_status, encryption_key
    else:
        # Insert new system info if no record exists for this agent_id
        try:
            external_ip = get_external_ip()
            encryption_key = Fernet.generate_key().decode()
            logging.debug(f"Generated encryption key for new agent: {encryption_key}")
            insert_data = {
                'agent_id': agent_id,
                'hostname': hostname,
                'ip': ip,
                'os': os_info,
                'timeout_interval': DEFAULT_TIMEOUT,
                'check_in': DEFAULT_CHECK_IN,
                'last_checked_in': now,
                'username': '',  # Default empty string for username
                'localuser': local_user,
                'encryption_key': encryption_key
            }
            if external_ip:
                insert_data['external_ip'] = external_ip

            with_retries(lambda: supabase.table('settings').insert(insert_data).execute())
        except Exception as e:  # Catch all exceptions during insert
            logging.error(f"An error occurred while inserting settings: {e}")

    return DEFAULT_TIMEOUT, DEFAULT_CHECK_IN, encryption_key