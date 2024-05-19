# Project Structure Overview

## Client

* [supaseaclient.py](supaseaclient.md): Main client script handling interactions with the Supabase backend.
* utils/: Utility functions for the client side, including:
  * [upload.py](upload.md): Functions for uploading files.
  * [database.py](database.md): Database interaction functions.
  * [download.py](download.md): Functions for downloading files.
  * [login.py](login.md): User authentication and login functions.
  * [commands.py](commands.md): Command execution functions for the client.

## Agent

* utils/: Utility functions for the agent side, including:
  * retry_utils.py: Functions for retry logic.
  * config.py: Configuration settings for the agent.
  * system_info.py: Functions for retrieving system information.
  * [agent_status.py](agent_status.md): Functions for updating agent status.
  * settings.py: Configuration settings for the agent.
    * winapi/: Native Windows API functions, including:
    * [run.py](run.md): Function to run commands.
    * smb_write.py: SMB write functions.
    * list_users_in_group.py: Functions to list users in a specific group.
    * format_file_info.py: Functions to format file information.
    * wami.py: Functions to retrieve system information.
    * ls.py: Functions to list directory contents.
    * [netexec.py](netexec.md): Functions to execute .NET assemblies.
    * get_file_attributes_string.py: Functions to get file attributes.
    * pwd.py: Functions to get the current directory.
    * smb_get.py: SMB get functions.
    * ps.py: Functions to list processes.
    * winrm_execute.py: Functions to execute commands via WinRM.
