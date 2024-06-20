import wmi

def wmirun(hostname, command, user=None, password=None, domain=None):
    """Executes a command on a remote machine via WMI."""
    try:
        # Construct the connection string
        if user and password:
            connection = wmi.WMI(
                computer=hostname,
                user=f"{domain}\\{user}" if domain else user,
                password=password
            )
        else:
            connection = wmi.WMI(computer=hostname)

        # Execute the command
        process_startup = connection.Win32_ProcessStartup.new()
        process_id, result = connection.Win32_Process.Create(
            CommandLine=command,
            ProcessStartupInformation=process_startup
        )

        if result == 0:
            return f"Process started successfully with PID: {process_id}"
        else:
            return f"Failed to start process. Error code: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
