import logging
import time
import random
import uuid  # Import the uuid module
from utils.agent_status import reset_agent_status, update_settings_status
from utils.settings import fetch_settings, fetch_agent_id_by_hostname
from utils.command_execution import execute_commands
from utils.retry_utils import with_retries
from utils.system_info import get_system_info

# Configure logging
logging.basicConfig(level=logging.WARN)

# Generate a unique identifier for this agent instance
hostname, ip, os_info = get_system_info()
agent_id = fetch_agent_id_by_hostname(hostname)
if not agent_id:
    agent_id = str(uuid.uuid4())

if __name__ == "__main__":
    reset_agent_status(agent_id)
    while True:
        settings = with_retries(lambda: fetch_settings(agent_id))
        if settings:
            timeout_interval, _ = settings
        else:
            # Default timeout interval if fetching settings fails
            timeout_interval = 10
            logging.warning("Using default timeout interval due to fetch_settings failure.")

        with_retries(lambda: execute_commands(agent_id))  # Pass the agent_id to execute_commands

        interval = random.randint(1, timeout_interval)
        time.sleep(interval)
