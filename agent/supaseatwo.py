import logging
import time
import random
from utils.agent_status import reset_agent_status, update_settings_status
from utils.settings import fetch_settings
from utils.command_execution import execute_commands
from utils.config import supabase

if __name__ == "__main__":
    reset_agent_status(supabase)
    while True:
        timeout_interval, _ = fetch_settings(supabase)
        execute_commands(supabase)
        interval = random.randint(1, timeout_interval)
        time.sleep(interval)