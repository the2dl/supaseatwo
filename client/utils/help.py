# help.py

# ANSI escape codes for colors
GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'
BLUE = '\033[34m'

# Define detailed help information for each command
detailed_help = {
    "sleep": {
        "description": "Sets a custom timeout for your agent.",
        "command": "sleep",
        "parameters": "numerical value in seconds",
        "example": "sleep 5"
    },
    "ps": {
        "description": "Lists all processes or filters them by name or terminates a process by ID.",
        "command": "ps",
        "parameters": "<none> or grep <pattern> or term <processid>",
        "example": "ps\nps grep notepad\nps term 1234"
    },
    "run": {
        "description": "Launches a process from a remote file.",
        "command": "run",
        "parameters": "path_to_remote_file",
        "example": "run C:\\path\\to\\file.exe"
    },
    "ls": {
        "description": "Lists the contents of a directory.",
        "command": "ls",
        "parameters": "directory_path",
        "example": "ls C:\\Users\\"
    },
    "mv": {
        "description": "Moves a file or directory to a new location.",
        "command": "mv",
        "parameters": "source destination",
        "example": "mv C:\\path\\to\\file.txt D:\\newpath\\file.txt"
    },
    "cat": {
        "description": "Displays the contents of a file.",
        "command": "cat",
        "parameters": "file_path",
        "example": "cat C:\\path\\to\\file.txt"
    },
    "cp": {
        "description": "Copies a file or directory to a new location.",
        "command": "cp",
        "parameters": "source destination",
        "example": "cp C:\\path\\to\\file.txt D:\\newpath\\file.txt"
    },
    "mkdir": {
        "description": "Creates a new directory.",
        "command": "mkdir",
        "parameters": "directory_path",
        "example": "mkdir C:\\new\\directory"
    },
    "cd": {
        "description": "Changes the current directory.",
        "command": "cd",
        "parameters": "directory_path",
        "example": "cd C:\\new\\directory"
    },
    "rm": {
        "description": "Removes a file or directory.",
        "command": "rm",
        "parameters": "path",
        "example": "rm C:\\path\\to\\file.txt"
    },
    "get_ad_domain": {
        "description": "Retrieves the Active Directory domain name.",
        "command": "get_ad_domain",
        "parameters": "none",
        "example": "get_ad_domain"
    },
    "get_dc_list": {
        "description": "Retrieves the list of domain controllers.",
        "command": "get_dc_list",
        "parameters": "none",
        "example": "get_dc_list"
    },
    "get_logged_on_users": {
        "description": "Retrieves the list of users currently logged on.",
        "command": "get_logged_on_users",
        "parameters": "none",
        "example": "get_logged_on_users"
    },
    "get_installed_programs": {
        "description": "Retrieves the list of installed programs.",
        "command": "get_installed_programs",
        "parameters": "none",
        "example": "get_installed_programs"
    },
    "get_drive_info": {
        "description": "Retrieves information about all the drives in the system.",
        "command": "get_drive_info",
        "parameters": "none",
        "example": "get_drive_info"
    },
    "whoami": {
        "description": "Displays user information (on Windows, use /all for detailed info).",
        "command": "whoami",
        "parameters": "none",
        "example": "whoami"
    },
    "pwd": {
        "description": "Displays the current working directory.",
        "command": "pwd",
        "parameters": "none",
        "example": "pwd"
    },
    "hostname": {
        "description": "Retrieves the local hostname.",
        "command": "hostname",
        "parameters": "none",
        "example": "hostname"
    },
    "ipinfo": {
        "description": "Retrieves local interface details.",
        "command": "ipinfo",
        "parameters": "none",
        "example": "ipinfo"
    },
    "nslookup": {
        "description": "Performs a DNS lookup for the given hostname.",
        "command": "nslookup",
        "parameters": "hostname",
        "example": "nslookup example.com"
    },
    "compress": {
        "description": "Compresses a file into <=50MB chunks, stored in C:\\ProgramData\\Microsoft\\chunk.",
        "command": "compress",
        "parameters": "file_path",
        "example": "compress C:\\path\\to\\file.txt"
    },
    "download": {
        "description": "Downloads a file from the asset.",
        "command": "download",
        "parameters": "file_path",
        "example": "download C:\\path\\to\\file.txt"
    },
    "upload": {
        "description": "Uploads a file to the asset.",
        "command": "upload",
        "parameters": "local_path remote_path",
        "example": "upload C:\\local\\file.txt C:\\remote\\path\\file.txt"
    },
    "users": {
        "description": "Lists users in the specified local or domain group.",
        "command": "users",
        "parameters": "<local|dom> <groupname> or <domain\\group_name>",
        "example": "users local Administrators\nusers dom Domain\\Admins"
    },
    "make_token": {
        "description": "Creates a new security token and impersonates the user.",
        "command": "make_token",
        "parameters": "username password [domain]",
        "example": "make_token user1 P@ssw0rd DOMAIN"
    },
    "revert_to_self": {
        "description": "Reverts to the original security context.",
        "command": "revert_to_self",
        "parameters": "none",
        "example": "revert_to_self"
    },
    "netexec": {
        "description": "Runs a .NET assembly in-memory.",
        "command": "netexec",
        "parameters": "local_file arguments",
        "example": "netexec C:\\path\\to\\assembly.exe args"
    },
    "getsmb": {
        "description": "Gets a file from a remote host via SMB protocol.",
        "command": "getsmb",
        "parameters": "remote_file_path local_file_path [username password domain]",
        "example": "getsmb \\\\remote\\share\\file.txt C:\\local\\file.txt user pass domain"
    },
    "writesmb": {
        "description": "Writes a file to a remote host via SMB protocol.",
        "command": "writesmb",
        "parameters": "local_file_path remote_smb_path [username password domain]",
        "example": "writesmb C:\\local\\file.txt \\\\remote\\share\\file.txt user pass domain"
    },
    "winrmexec": {
        "description": "Executes a command on a remote host via WinRM.",
        "command": "winrmexec",
        "parameters": "remote_host command [username password domain]",
        "example": "winrmexec remote_host ipconfig user pass domain"
    },
    "link smb agent": {
        "description": "Links the SMB agent to the current host using the specified IP address, optionally with credentials.",
        "command": "link smb agent",
        "parameters": "ip_address [username password domain]",
        "example": "link smb agent 192.168.1.1 user pass domain"
    },
    "unlink smb agent": {
        "description": "Unlinks the SMB agent from the current host using the specified IP address.",
        "command": "unlink smb agent",
        "parameters": "ip_address",
        "example": "unlink smb agent 192.168.1.1"
    },
    "injectshellcode": {
        "description": "Injects and executes shellcode in explorer.exe.",
        "command": "injectshellcode",
        "parameters": "file_path",
        "example": "injectshellcode C:\\path\\to\\shellcode.bin"
    },
    "inject_memory": {
        "description": "Uploads shellcode file and injects it into explorer.exe.",
        "command": "inject_memory",
        "parameters": "local_path",
        "example": "inject_memory C:\\path\\to\\shellcode.bin"
    },
    "list_scheduled_tasks": {
        "description": "Lists all scheduled tasks.",
        "command": "list_scheduled_tasks",
        "parameters": "none",
        "example": "list_scheduled_tasks"
    },
    "create_scheduled_task": {
        "description": "Creates a scheduled task.",
        "command": "create_scheduled_task",
        "parameters": "task_name command_line trigger_time [repeat_interval] [repeat_duration]",
        "example": "create_scheduled_task MyTask 'C:\\path\\to\\app.exe' '2024-06-01T12:00:00' 'PT1H' 'P1D'"
    },
    "delete_scheduled_task": {
        "description": "Deletes a scheduled task.",
        "command": "delete_scheduled_task",
        "parameters": "task_name",
        "example": "delete_scheduled_task MyTask"
    },
    "get_scheduled_task_info": {
        "description": "Retrieves information about a scheduled task.",
        "command": "get_scheduled_task_info",
        "parameters": "task_name",
        "example": "get_scheduled_task_info MyTask"
    },
    "start_scheduled_task": {
        "description": "Starts a scheduled task.",
        "command": "start_scheduled_task",
        "parameters": "task_name",
        "example": "start_scheduled_task MyTask"
    },
    "view_history": {
        "description": "Views the command history for the current host.",
        "command": "view_history",
        "parameters": "none or grep <term>",
        "example": "view_history\nview_history grep term"
    },
    "kill": {
        "description": "Terminates the agent.",
        "command": "kill",
        "parameters": "none",
        "example": "kill"
    },
    "exit": {
        "description": "Returns to the main menu.",
        "command": "exit",
        "parameters": "none",
        "example": "exit"
    }
}

# Function to display detailed help for a specific command
def display_detailed_help(command):
    if command in detailed_help:
        help_info = detailed_help[command]
        print("\nCommand Help:")
        print(f" Description  : {help_info['description']}")
        print(f" Command      : {help_info['command']}")
        print(f" Parameters   : {help_info['parameters']}")
        print(f" Example      : {help_info['example']}\n")
    else:
        print(f"No detailed help available for command: {command}")

# Function to display general help menu
def display_help(command_mappings):
    print("\nAvailable Shortcut Commands:")
    for shortcut, command in command_mappings.items():
        print(f" {shortcut:<10}        :: {command}")
    print(" sleep <number>                :: Set a custom timeout (ex. sleep 5)")
    print(" ps                            :: List all processes")
    print(" ps grep <pattern>             :: Filter processes by name")
    print(" ps term <processid>           :: Terminate a process by its process ID")
    print(" run <path_to_remote_file>     :: Launch a process")
    print(" ls <directory_path>           :: List contents of a directory")
    print(" mv <source> <destination>     :: Move a file or directory")
    print(" cat <file_path>               :: Display the contents of a file")
    print(" cp <source> <destination>     :: Copy a file or directory")
    print(" mkdir <directory_path>        :: Create a new directory")
    print(" cd <directory_path>           :: Change current directory")
    print(" rm <path>                     :: Remove a file or directory")
    print(" get_ad_domain                 :: Retrieve the Active Directory domain name")
    print(" get_dc_list                   :: Retrieve the list of domain controllers")
    print(" get_logged_on_users           :: Retrieve the list of users currently logged on")
    print(" get_installed_programs        :: Retrieve the list of installed programs")
    print(" get_drive_info                :: Retrieve information about all the drives in the system")
    print(" whoami                        :: Display user information (on Windows /all)")
    print(" pwd                           :: Display current working directory")
    print(" hostname                      :: Retrieve the local hostname")
    print(" ipinfo                        :: Retrieve local interface details")
    print(" nslookup <hostname>           :: Perform a DNS lookup for the given hostname")
    print(" compress <file_path>          :: Compress a file into <=50MB chunks, stored in C:\\ProgramData\\Microsoft\\chunk")
    print(" download <file_path>          :: Download a file from the asset")
    print(" upload <local_path> <remote_path> :: Upload a file to the asset")
    print(" users <local|dom> <groupname> or <domain\\group_name> :: List users in the specified local or domain group")
    print(" make_token <username> <password> [domain] :: Create a new security token and impersonate the user")
    print(" revert_to_self                :: Revert to the original security context")
    print(" netexec <local_file> <arguments> :: Run a .NET assembly in-memory")
    print(" getsmb <remote_file_path> <local_file_path> [username password domain]  :: Get a file from a remote host via SMB protocol")
    print(" writesmb <local_file_path> <remote_smb_path> [username password domain] :: Write a file to a remote host via SMB protocol")
    print(" winrmexec <remote_host> <command> [username password domain] :: Execute a command on a remote host via WinRM")
    print(" link smb agent <ip_address> [username password domain]  :: Link the SMB agent to the current host using the specified IP address, optionally with credentials")
    print(" unlink smb agent <ip_address> :: Unlink the SMB agent from the current host using the specified IP address")
    print(" injectshellcode <file_path>   :: Inject and execute shellcode in explorer.exe")
    print(" inject_memory <local_path>    :: Upload shellcode file and inject it into explorer.exe")
    print(" list_scheduled_tasks          :: List all scheduled tasks")
    print(" create_scheduled_task <task_name> <command_line> <trigger_time> [repeat_interval] [repeat_duration] :: Create a scheduled task")
    print(" delete_scheduled_task <task_name> :: Delete a scheduled task")
    print(" get_scheduled_task_info <task_name> :: Retrieve information about a scheduled task")
    print(" start_scheduled_task <task_name> :: Start a scheduled task")
    print(" view_history                  :: View the command history for the current host")
    print(" view_history grep <term>      :: Search the command history for the current host with a specific term")
    print(" kill                          :: Terminate the agent")
    print(" exit                          :: Return to main menu\n")