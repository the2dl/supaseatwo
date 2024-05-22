import logging
from datetime import datetime
from .system_info import get_system_info
from .config import supabase, SUPABASE_URL, SUPABASE_KEY, DEFAULT_TIMEOUT, DEFAULT_CHECK_IN
from .retry_utils import with_retries

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
            with_retries(lambda: supabase.table('settings').insert({
                'hostname': hostname,
                'ip': ip,
                'os': os_info,
                'timeout_interval': DEFAULT_TIMEOUT,
                'check_in': DEFAULT_CHECK_IN,
                'last_checked_in': now,
                'username': ''  # Default empty string for username
            }).execute())
        except Exception as e:  # Catch all exceptions during insert
            logging.error(f"An error occurred while inserting settings: {e}")

    return DEFAULT_TIMEOUT, DEFAULT_CHECK_IN
