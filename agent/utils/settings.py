import logging
import httpx
from datetime import datetime
from .system_info import get_system_info
from .config import supabase, DEFAULT_TIMEOUT, DEFAULT_CHECK_IN
from .retry_utils import with_retries

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

def fetch_settings():
    """Fetch the system settings from the settings table, or return default values."""
    hostname, ip, os_info = get_system_info()
    response = with_retries(lambda: supabase.table('settings').select('*').eq('hostname', hostname).limit(1).execute())
    settings_data = response.data

    now = datetime.utcnow().isoformat() + "Z"  # Timestamp in UTC format

    if settings_data:
        settings = settings_data[0]
        timeout_interval = settings.get('timeout_interval', DEFAULT_TIMEOUT)
        check_in_status = settings.get('check_in', DEFAULT_CHECK_IN)
        external_ip = settings.get('external_ip')

        # Fetch external IP if not already stored
        if not external_ip:
            external_ip = get_external_ip()
            if external_ip:
                try:
                    with_retries(lambda: supabase.table('settings').update({
                        'external_ip': external_ip
                    }).eq('hostname', hostname).execute())
                except Exception as e:
                    logging.warning(f"Failed to update external IP: {e}")

        # Try updating the last checked-in time with error handling
        try:
            with_retries(lambda: supabase.table('settings').update({
                'last_checked_in': now
            }).eq('hostname', hostname).execute())
        except Exception as e:
            logging.warning(f"Failed to update last checked-in time: {e}")

        return timeout_interval, check_in_status
    else:
        # Insert new system info if no record exists for this hostname
        try:
            external_ip = get_external_ip()
            insert_data = {
                'hostname': hostname,
                'ip': ip,
                'os': os_info,
                'timeout_interval': DEFAULT_TIMEOUT,
                'check_in': DEFAULT_CHECK_IN,
                'last_checked_in': now,
                'username': '',  # Default empty string for username
            }
            if external_ip:
                insert_data['external_ip'] = external_ip

            with_retries(lambda: supabase.table('settings').insert(insert_data).execute())
        except Exception as e:  # Catch all exceptions during insert
            logging.error(f"An error occurred while inserting settings: {e}")

    return DEFAULT_TIMEOUT, DEFAULT_CHECK_IN