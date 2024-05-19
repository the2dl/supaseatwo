# SupaseaTwo

This script serves as the main agent interface for interacting with the Supabase backend. It handles resetting the agent status, fetching settings, executing commands, and updating the settings status.

## Functions:
* reset_agent_status: Resets the agent status in the Supabase database.
* fetch_settings: Fetches the settings from the Supabase database.
* execute_commands: Executes commands received from the Supabase database.
* update_settings_status: Updates the status of the settings in the Supabase database.
* with_retries: A decorator to retry a function call on failure.