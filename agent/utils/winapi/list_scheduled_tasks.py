import win32com.client

def list_scheduled_tasks():
    """Lists all scheduled tasks."""
    try:
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')
        tasks = root_folder.GetTasks(0)
        
        task_list = []
        for task in tasks:
            task_list.append(f"Task Name: {task.Name}, State: {task.State}")
        
        return task_list
    except Exception as e:
        return [f"Error: {str(e)}"]
