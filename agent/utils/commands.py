from supabase import create_client
from .config import supabase, SUPABASE_URL, SUPABASE_KEY
from .retry_utils import with_retries

# Initialize Supabase client
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # This is redundant since we are importing it from config

def fetch_pending_commands_for_hostname(hostname):
    """Fetch commands with status 'Pending' and a specific hostname."""
    return with_retries(lambda: supabase.table('py2').select('*').eq('status', 'Pending').eq('hostname', hostname).execute())

def update_command_status(command_id, status, output='', hostname='', ip='', os='', username='', smbhost=''):
    """Updates the status of a command in the py2 table."""
    command_data = {
        'status': status,
        'output': output,
        'hostname': hostname or '',
        'ip': ip or '',
        'os': os or '',
    }

    # Conditionally add the 'username' and 'smbhost' fields
    if username:
        command_data['username'] = username
    if smbhost:
        command_data['smbhost'] = smbhost

    with_retries(lambda: supabase.table('py2').update(command_data).eq('id', command_id).execute())
