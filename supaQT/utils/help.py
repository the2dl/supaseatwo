from PyQt5.QtCore import QObject, pyqtSignal

class HelpManager(QObject):
    help_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.detailed_help = {
            "sleep": {
                "description": "Sets a custom timeout for your agent.",
                "command": "sleep",
                "parameters": "numerical value in seconds",
                "example": "sleep 5"
            },
            "ps": {
                "description": "Lists all processes.",
                "command": "ps",
                "parameters": "<none>",
                "example": "ps"
            },
            "ps grep": {
                "description": "Lists all processes and filters them by name.",
                "command": "ps",
                "parameters": "grep <pattern>",
                "example": "ps grep notepad"
            },
            "ps term": {
                "description": "Terminates a process by ID.",
                "command": "ps",
                "parameters": "term <processid>",
                "example": "ps term 1234"
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
            # Add all other commands from the old code here
            # ...
            "exit": {
                "description": "Returns to the main menu.",
                "command": "exit",
                "parameters": "none",
                "example": "exit"
            }
        }

    def display_help(self, command_mappings):
        help_text = "Available Commands:\n"
        help_text += "=" * 80 + "\n\n"
        
        for command in sorted(self.detailed_help.keys()):
            help_info = self.detailed_help[command]
            help_text += f"{command:<15} :: {help_info['description']}\n"
            help_text += f"{'':5}Usage   : {help_info['command']} {help_info['parameters']}\n"
            help_text += f"{'':5}Example : {help_info['example']}\n\n"
        
        self.help_signal.emit(help_text)
        return help_text

    def display_detailed_help(self, command):
        if command in self.detailed_help:
            help_info = self.detailed_help[command]
            help_text = f"Command Help: {command}\n"
            help_text += "=" * 80 + "\n\n"
            help_text += f"Description : {help_info['description']}\n"
            help_text += f"Usage       : {help_info['command']} {help_info['parameters']}\n"
            help_text += f"Example     : {help_info['example']}\n"
        else:
            help_text = f"No detailed help available for command: {command}\n"
        
        self.help_signal.emit(help_text)
        return help_text

help_manager = HelpManager()

def display_detailed_help(command):
    return help_manager.display_detailed_help(command)

def display_help(command_mappings):
    return help_manager.display_help(command_mappings)