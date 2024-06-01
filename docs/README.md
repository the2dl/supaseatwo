# Project Structure Overview

## Install instructions

* [Detailed install instructions](install.md): Full installation material to get supaseatwo functional.

## Client

* [supaseaclient.py](supaseaclient.md): Main client script handling interactions with the Supabase backend.
* utils/: Utility functions for the client side, including:
  * [upload.py](upload.md): Functions for uploading files.
  * [database.py](database.md): Database interaction functions.
  * [download.py](download.md): Functions for downloading files.
  * [login.py](login.md): User authentication and login functions.
  * [commands.py](commands.md): Command execution functions for the client.

## Agent

* [supaseatwo.py](supaseatwo.md): Main agent script handling backend communications.
* [smb_agent.py](smb_agent.md): SMB agent script handling various commands and file operations.
* utils/: Utility functions for the agent side, including:
  * [command_execution.py](command_execution.md): Command execution and management functions.
  * [ai_summary.py](ai_summary.md): Functions for generating AI-based summaries of command outputs.
  * [retry_utils.py](retry_utils.md): Functions for retry logic.
  * [config.py](config.md): Configuration settings for the agent.
  * [system_info.py](system_info.md): Functions for retrieving system information.
  * [agent_status.py](agent_status.md): Functions for updating agent status.
  * [settings.py](settings.md): Configuration settings for the agent.
  * [commands.py](agent_commands.md): Command execution functions for the agent.
  * [file_operations.py](file_operations.md): Handle file uploads and downloads, interacting with Supabase storage, and managing command statuses.
      * winapi/: Native Windows API functions, including:
      * [run.py](run.md): Function to run commands.
      * [smb_write.py](smb_write.md): SMB write functions.
      * [list_users_in_group.py](list_users_in_group.md): Functions to list users in a specific group.
      * [format_file_info.py](format_file_info.md): Functions to format file information.
      * [wami.py](wami.md): Functions to retrieve system information.
      * [ls.py](ls.md): Functions to list directory contents.
      * [netexec.py](netexec.md): Functions to execute .NET assemblies.
      * [get_file_attributes_string.py](get_file_attributes_string.md): Functions to get file attributes.
      * [pwd.py](pwd.md): Functions to get the current directory.
      * [smb_get.py](smb_get.md): SMB get functions.
      * [ps.py](ps.md): Functions to list processes.
      * [winrm_execute.py](winrm_execute.md): Functions to execute commands via WinRM.
      * [mv.py](mv.md): Functions to move files.
      * [load_shellcode_from_url.py](load_shellcode_from_url.md): Functions to load shellcode from a URL.
      * [cp.py](cp.md): Functions to copy files.
      * [rm.py](rm.md): Functions to remove files.
      * [mkdir.py](mkdir.md): Functions to create directories.
      * [inject_shellcode.py](inject_shellcode.md): Functions to inject shellcode into a process.
      * [hostname.py](hostname.md): Functions to retrieve the hostname of the machine.
      * [nslookup.py](nslookup.md): Functions to perform DNS lookup.



