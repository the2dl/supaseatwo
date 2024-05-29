import logging
import time
import random
from utils.agent_status import reset_agent_status, update_settings_status
from utils.settings import fetch_settings
from utils.command_execution import execute_commands
from utils.retry_utils import with_retries

# Configure logging
logging.basicConfig(level=logging.WARN)

if __name__ == "__main__":
    reset_agent_status()
    while True:
        settings = with_retries(fetch_settings)
        if settings:
            timeout_interval, _ = settings
        else:
            # Default timeout interval if fetching settings fails
            timeout_interval = 10
            logging.warning("Using default timeout interval due to fetch_settings failure.")

        with_retries(execute_commands)  # No need to pass supabase

        interval = random.randint(1, timeout_interval)
        time.sleep(interval)
