import logging
from cryptography.fernet import Fernet
from .database import supabase

def fetch_agent_info_by_hostname(hostname):
    """Fetch the agent_id and encryption key using hostname from the settings table."""
    try:
        response = supabase.table('settings').select('agent_id', 'encryption_key').eq('hostname', hostname).execute()
        if response.data:
            agent_info = response.data[0]
            encryption_key = agent_info.get('encryption_key')
            if encryption_key:
                encryption_key = encryption_key.encode()
            return agent_info['agent_id'], encryption_key
        else:
            print(f"No agent_id found for hostname: {hostname}")
            return None, None
    except Exception as e:
        print(f"An error occurred while fetching agent info for hostname {hostname}: {e}")
        return None, None

def encrypt_response(response, key):
    try:
        logging.info(f"Encrypting response using key: {key}")
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(response.encode()).decode()
        logging.info(f"Encrypted response: {encrypted_data}")
        return encrypted_data
    except Exception as e:
        logging.error(f"Failed to encrypt response: {e}")
        return f"Failed to encrypt response: {e}"

def decrypt_output(encrypted_output, key):
    try:
        logging.info(f"Decrypting output using key: {key}")
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_output.encode()).decode()
        logging.info(f"Decrypted output: {decrypted_data}")
        return decrypted_data
    except Exception as e:
        logging.error(f"Failed to decrypt output: {e}")
        return f"Failed to decrypt output: {e}"