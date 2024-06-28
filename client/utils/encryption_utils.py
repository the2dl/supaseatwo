import logging
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from .database import supabase

#logging.basicConfig(level=logging.DEBUG)

def fetch_agent_info_by_hostname(hostname):
    """Fetch the agent_id and encryption key using hostname from the settings table."""
    try:
        response = supabase.table('settings').select('agent_id', 'encryption_key').eq('hostname', hostname).execute()
        if response.data:
            agent_info = response.data[0]
            encryption_key = agent_info.get('encryption_key')
            if encryption_key:
                # Decode the base64 string
                encryption_key = base64.b64decode(encryption_key)
                logging.debug(f"Decoded key length: {len(encryption_key)} bytes")
                # Use only the first 32 bytes of the key
                encryption_key = encryption_key[:32]
                logging.debug(f"Trimmed key length: {len(encryption_key)} bytes")
            return agent_info['agent_id'], encryption_key
        else:
            logging.error(f"No agent_id found for hostname: {hostname}")
            return None, None
    except Exception as e:
        logging.error(f"An error occurred while fetching agent info for hostname {hostname}: {e}")
        return None, None

def encrypt_message(message, key):
    try:
        logging.debug(f"Encrypting message. Key length: {len(key)} bytes")
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
        encrypted_data = cipher.nonce + tag + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to encrypt message: {e}")
        raise

def decrypt_message(encrypted_message, key):
    try:
        logging.debug(f"Decrypting message. Key length: {len(key)} bytes")
        encrypted_data = base64.b64decode(encrypted_message)
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to decrypt message: {e}")
        raise