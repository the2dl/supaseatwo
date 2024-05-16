import winrm
from utils.retry_utils import with_retries

def winrm_execute(remote_host, command, username=None, password=None, domain=None):
    """Executes a command on a remote host using WinRM."""
    def winrm_operation():
        if domain:
            full_username = f"{domain}\\{username}"
        else:
            full_username = username

        session = winrm.Session(
            f'http://{remote_host}:5985/wsman',
            auth=(full_username, password),
            transport='ntlm' if domain else 'plaintext'
        )
        result = session.run_cmd(command)

        if result.status_code == 0:
            return f"Successfully executed command on {remote_host}:\n{result.std_out.decode()}"
        else:
            return f"Error executing command on {remote_host}:\n{result.std_err.decode()}"

    try:
        return with_retries(winrm_operation)
    except Exception as e:
        return f"Error: {str(e)}"