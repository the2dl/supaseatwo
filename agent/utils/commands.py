from supabase import Client
from .config import SUPABASE_URL, SUPABASE_KEY
from .retry_utils import with_retries

supabase = Client(SUPABASE_URL, SUPABASE_KEY)

def fetch_pending_commands_for_hostname(hostname, supabase):  # Add supabase as an argument
    """Fetch commands with status 'Pending' and a specific hostname."""
    return with_retries(lambda: supabase.table('py2').select('*').eq('status', 'Pending').eq('hostname', hostname).execute())

def update_command_status(supabase, command_id, status, output='', hostname='', ip='', os='', username=''):
    """Updates the status of a command in the py2 table."""
    command_data = {
        'status': status,
        'output': output,
        'hostname': hostname or '',
        'ip': ip or '',
        'os': os or '',
    }

    # Conditionally add the 'username' field
    if username:
        command_data['username'] = username

    with_retries(lambda: supabase.table('py2').update(command_data).eq('id', command_id).execute())