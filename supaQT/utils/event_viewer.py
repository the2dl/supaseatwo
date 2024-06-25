import logging
from PyQt5.QtCore import QObject, pyqtSignal
from utils.database import db_manager
from utils.encryption_utils import encryption_manager

class EventViewer(QObject):
    new_event = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def fetch_events(self, hostname, limit=50):
        response = db_manager.get_command_history(hostname, limit)
        events = response.data
        formatted_events = []

        # Fetch the encryption key for this hostname
        encryption_key = self.get_encryption_key(hostname)
        if not encryption_key:
            self.new_event.emit(f"Warning: Unable to fetch encryption key for {hostname}")
            return []

        for event in events:
            formatted_event = self.format_event(event, encryption_key)
            formatted_events.append(formatted_event)
            self.new_event.emit(formatted_event)

        return formatted_events

    def get_encryption_key(self, hostname):
        settings = db_manager.get_host_settings(hostname)
        if settings and 'encryption_key' in settings:
            return settings['encryption_key'].encode()
        logging.warning(f"No encryption key found for hostname: {hostname}")
        return None

    def format_event(self, event, encryption_key):
        created_at = event['created_at']
        username = event['username']
        ip = event.get('ip', 'N/A')
        command = event.get('command', '')
        output = event.get('output', '')
        ai_summary = event.get('ai_summary', 'No summary available')

        # Use smbhost if it exists, otherwise use hostname
        hostname = event.get('smbhost') or event['hostname']

        try:
            if command:
                command = encryption_manager.decrypt(command, encryption_key)
            if output:
                output = encryption_manager.decrypt(output, encryption_key)
            if ai_summary and ai_summary != 'No summary available':
                ai_summary = encryption_manager.decrypt(ai_summary, encryption_key)
        except Exception as e:
            logging.error(f"Error decrypting event data for {hostname}: {e}")
            command = "Error: Unable to decrypt command"
            output = "Error: Unable to decrypt output"
            ai_summary = "Error: Unable to decrypt AI summary"

        formatted_event = (
            f"Time: {created_at}\n"
            f"User: {username}\n"
            f"IP: {ip}\n"
            f"Hostname: {hostname}\n"
            f"Command: {command}\n"
            f"Output: {output}\n"
            f"AI Summary: {ai_summary}\n"
            f"{'-' * 50}\n"
        )

        return formatted_event

    def search_events(self, hostname, search_term, limit=50):
        events = self.fetch_events(hostname, limit)
        filtered_events = [event for event in events if search_term.lower() in event.lower()]
        return filtered_events

    def add_new_event(self, event_data):
        encryption_key = self.get_encryption_key(event_data['hostname'])
        if encryption_key:
            formatted_event = self.format_event(event_data, encryption_key)
            self.new_event.emit(formatted_event)
        else:
            self.new_event.emit(f"Error: Unable to add new event for {event_data['hostname']}")

    def clear_events(self):
        self.new_event.emit("CLEAR")