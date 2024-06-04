import win32com.client

def delete_scheduled_task(task_name):
    """Deletes a scheduled task."""
    try:
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')
        root_folder.DeleteTask(task_name, 0)
        
        return [f"Scheduled task '{task_name}' deleted successfully."]
    except Exception as e:
        return [f"Error: {str(e)}"]
