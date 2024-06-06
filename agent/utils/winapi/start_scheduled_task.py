import win32com.client

def start_scheduled_task(task_name):
    """Starts a scheduled task."""
    try:
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')
        task = root_folder.GetTask(task_name)
        task.Run("")
        return [f"Task '{task_name}' started successfully."]
    except Exception as e:
        return [f"Error: {str(e)}"]
