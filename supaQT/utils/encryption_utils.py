import logging
from cryptography.fernet import Fernet
from utils.database import db_manager

class EncryptionManager:
    @staticmethod
    def encrypt(data, key):
        if not data or not key:
            logging.warning("Empty data or key provided for encryption")
            return None
        try:
            f = Fernet(key)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            return None

    @staticmethod
    def decrypt(encrypted_data, key):
        if not encrypted_data or not key:
            logging.warning("Empty encrypted data or key provided for decryption")
            return None
        try:
            f = Fernet(key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return None

    @staticmethod
    def fetch_agent_info_by_hostname(hostname):
        """Fetch the agent_id and encryption key using hostname from the settings table."""
        try:
            settings = db_manager.get_host_settings(hostname)
            if settings:
                agent_id = settings.get('agent_id')
                encryption_key = settings.get('encryption_key')
                if encryption_key:
                    encryption_key = encryption_key.encode()
                return agent_id, encryption_key
            else:
                logging.error(f"No agent info found for hostname: {hostname}")
                return None, None
        except Exception as e:
            logging.error(f"An error occurred while fetching agent info for hostname {hostname}: {e}")
            return None, None

    @staticmethod
    def get_encryption_key(hostname):
        """Fetch the encryption key for a given hostname."""
        _, encryption_key = EncryptionManager.fetch_agent_info_by_hostname(hostname)
        return encryption_key

encryption_manager = EncryptionManager()

def encrypt_response(response, key):
    return encryption_manager.encrypt(response, key)

def decrypt_output(encrypted_output, key):
    return encryption_manager.decrypt(encrypted_output, key)

def fetch_agent_info_by_hostname(hostname):
    return encryption_manager.fetch_agent_info_by_hostname(hostname)

def get_encryption_key(hostname):
    return encryption_manager.get_encryption_key(hostname)