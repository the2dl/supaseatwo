import win32com.client
from datetime import datetime, timedelta
import shlex

def create_scheduled_task(task_name, command_line, trigger_time, repeat_interval=None, repeat_duration=None):
    """Creates a new scheduled task with the specified command line."""
    try:
        # Ensure the trigger time is in the correct ISO 8601 format
        dt = datetime.fromisoformat(trigger_time)
        start_boundary = dt.strftime('%Y-%m-%dT%H:%M:%S') + "Z"  # Append 'Z' for UTC time

        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')

        task_def = scheduler.NewTask(0)

        trigger = task_def.Triggers.Create(1)  # 1 means once
        trigger.StartBoundary = start_boundary
        trigger.Enabled = True

        # Correct repetition interval format
        if repeat_interval:
            interval_value = int(repeat_interval[:-1])  # Extract the numeric part
            interval_unit = repeat_interval[-1].upper()  # Extract the unit (W/D/H/M)
            if interval_unit == 'W':
                interval_days = interval_value * 7  # Convert weeks to days
                trigger.Repetition.Interval = f'P{interval_days}D'
            elif interval_unit == 'D':
                trigger.Repetition.Interval = f'P{interval_value}D'
            elif interval_unit == 'H':
                trigger.Repetition.Interval = f'PT{interval_value}H'
            elif interval_unit == 'M':
                interval_days = interval_value * 30  # Convert months to days
                trigger.Repetition.Interval = f'P{interval_days}D'
            else:
                raise ValueError("Invalid interval unit. Use 'W' for weeks, 'D' for days, 'H' for hours, or 'M' for months.")

        # Set repetition duration only if it's not forever
        if repeat_duration and repeat_duration.lower() != "forever":
            duration_value = int(repeat_duration[:-1])  # Extract the numeric part
            duration_unit = repeat_duration[-1].upper()  # Extract the unit (W/D/H/M)
            if duration_unit == 'W':
                duration_days = duration_value * 7  # Convert weeks to days
                trigger.Repetition.Duration = f'P{duration_days}D'
            elif duration_unit == 'D':
                trigger.Repetition.Duration = f'P{duration_value}D'
            elif duration_unit == 'H':
                trigger.Repetition.Duration = f'PT{duration_value}H'
            elif duration_unit == 'M':
                duration_days = duration_value * 30  # Convert months to days
                trigger.Repetition.Duration = f'P{duration_days}D'
            else:
                raise ValueError("Invalid duration unit. Use 'W' for weeks, 'D' for days, 'H' for hours, or 'M' for months.")

        # Split the command line into executable and arguments
        parts = shlex.split(command_line, posix=False)
        executable_path = parts[0]
        arguments = ' '.join(parts[1:])

        action = task_def.Actions.Create(0)  # 0 means execute
        action.Path = executable_path
        action.Arguments = arguments

        task_def.RegistrationInfo.Description = 'Created by Python script'  # Optional description

        task_def.Settings.Enabled = True
        task_def.Settings.StartWhenAvailable = True
        task_def.Settings.Hidden = False

        root_folder.RegisterTaskDefinition(
            task_name,
            task_def,
            6,  # TASK_CREATE_OR_UPDATE
            None,  # No user
            None,  # No password
            3  # CURRENT USER CONTEXT
        )

        return [f"Scheduled task '{task_name}' created successfully."]
    except Exception as e:
        return [f"Error: {str(e)}"]
