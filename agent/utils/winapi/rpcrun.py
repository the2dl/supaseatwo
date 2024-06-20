from pypsexec.client import Client

def rpcrun(hostname, command, user=None, password=None):
    """Executes a command on a remote machine via RPC using pypsexec, starting the process in the background."""
    try:
        print(f"Connecting to {hostname} with user: {user}")

        client = Client(hostname, username=user, password=password)
        client.connect()
        client.create_service()

        print(f"Executing command in the background: {command}")
        # Run the command in the background
        stdout, stderr, rc = client.run_executable(command, arguments="", timeout_seconds=0, asynchronous=True)

        client.remove_service()
        client.disconnect()

        return "Process started successfully in the background."
    except Exception as e:
        print(f"Exception occurred: {e}")
        return f"Error: {str(e)}"
