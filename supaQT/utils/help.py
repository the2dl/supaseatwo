from PyQt5.QtCore import QObject, pyqtSignal

class HelpManager(QObject):
    def display_help(self, command_mappings):
        help_text = "\nAvailable Shortcut Commands:\n"
        for shortcut, command in command_mappings.items():
            help_text += f" {shortcut:<10}        :: {command}\n"
        
        help_text += (
            " sleep <number>                :: Set a custom timeout (ex. sleep 5)\n"
            " ps                            :: List all processes\n"
            " ps grep <pattern>             :: Filter processes by name\n"
            " ps term <processid>           :: Terminate a process by its process ID\n"
            # ... (include all other command help lines here)
        )
        
        return help_text

    def display_detailed_help(self, command):
        if command in self.detailed_help:
            help_info = self.detailed_help[command]
            help_text = (
                f"\nCommand Help:\n"
                f" Description  : {help_info['description']}\n"
                f" Command      : {help_info['command']}\n"
                f" Parameters   : {help_info['parameters']}\n"
                f" Example      : {help_info['example']}\n"
            )
        else:
            help_text = f"No detailed help available for command: {command}"
        
        return help_text

help_manager = HelpManager()

def display_detailed_help(command):
    return help_manager.display_detailed_help(command)

def display_help(command_mappings):
    return help_manager.display_help(command_mappings)
