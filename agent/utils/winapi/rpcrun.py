from pypsexec.client import Client
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def rpcrun(hostname, command, user=None, password=None):

    try:
        logging.debug(f"Connecting to {hostname} with user: {user}")

        client = Client(hostname, username=user, password=password)
        client.connect()
        client.create_service()

        logging.debug(f"Executing command in the background: {command}")
        # Run the command in the background
        stdout, stderr, rc = client.run_executable(command, arguments="", timeout_seconds=0, asynchronous=True)

        client.remove_service()
        client.disconnect()

        return "Process started successfully in the background."
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        return f"Error: {str(e)}"
