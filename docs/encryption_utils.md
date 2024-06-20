# Encryption Utility Functions

This module provides functions to handle encryption and decryption of responses and outputs using the cryptography library, as well as fetching agent information from the settings table in Supabase.

## Functions:
* `fetch_agent_info_by_hostname`: Fetches the agent_id and encryption key using the hostname from the settings table.
* `encrypt_response`: Encrypts a response using the provided key.
* `decrypt_output`: Decrypts an encrypted output using the provided key.