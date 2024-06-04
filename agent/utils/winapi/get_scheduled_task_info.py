import win32com.client

def get_scheduled_task_info(task_name):
    """Retrieves the details of a specific scheduled task."""
    try:
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')
        task = root_folder.GetTask(task_name)
        
        task_info = []
        task_info.append(f"Task Name: {task.Name}")
        task_info.append(f"Task State: {task.State}")
        task_info.append(f"Last Run Time: {task.LastRunTime}")
        task_info.append(f"Next Run Time: {task.NextRunTime}")
        task_info.append(f"Number of Missed Runs: {task.NumberOfMissedRuns}")
        task_info.append(f"Last Task Result: {task.LastTaskResult}")
        
        # Get triggers
        triggers = task.Definition.Triggers
        for trigger in triggers:
            task_info.append(f"Trigger: {trigger.Type}")
            task_info.append(f"  Start Boundary: {trigger.StartBoundary}")
            task_info.append(f"  End Boundary: {trigger.EndBoundary}")
            task_info.append(f"  Enabled: {trigger.Enabled}")
            if trigger.Repetition.Interval:
                task_info.append(f"  Repetition Interval: {trigger.Repetition.Interval}")
            if trigger.Repetition.Duration:
                task_info.append(f"  Repetition Duration: {trigger.Repetition.Duration}")
        
        # Get actions
        actions = task.Definition.Actions
        for action in actions:
            task_info.append(f"Action: {action.Type}")
            task_info.append(f"  Path: {action.Path}")
            task_info.append(f"  Arguments: {action.Arguments}")
            task_info.append(f"  Working Directory: {action.WorkingDirectory}")
        
        return task_info
    except Exception as e:
        return [f"Error: {str(e)}"]
