import wmi
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def wmirun(hostname, command, user=None, password=None, domain=None):
    """Executes a command on a remote machine via WMI."""
    try:
        user_info = f"{domain}\\{user}" if domain else user
        logging.debug(f"Connecting to {hostname} with user: {user_info}")

        # Construct the connection string
        if user and password:
            connection = wmi.WMI(
                computer=hostname,
                user=user_info,
                password=password
            )
        else:
            connection = wmi.WMI(computer=hostname)

        logging.debug("Connection established successfully.")

        # Execute the command
        process_startup = connection.Win32_ProcessStartup.new()
        process_id, result = connection.Win32_Process.Create(
            CommandLine=command,
            ProcessStartupInformation=process_startup
        )

        if result == 0:
            logging.debug(f"Process started successfully with PID: {process_id}")
            return f"Process started successfully with PID: {process_id}"
        else:
            logging.error(f"Failed to start process. Error code: {result}")
            return f"Failed to start process. Error code: {result}"
    except wmi.x_wmi as wmi_exc:
        logging.error(f"WMI error: {str(wmi_exc)}")
        return f"WMI error: {str(wmi_exc)}"
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"
