from supabase import create_client, Client
from datetime import datetime, timedelta
import os

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', "https://aegfzwdrslyhgsugoecw.supabase.co")
SUPABASE_KEY = os.getenv('SUPABASE_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', "sk-proj-LQ5dm3iwTPD8Gkg3ys0ET3BlbkFJYrX98APv3iBjcHHRUNEU")

# Create a Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHECK_IN_THRESHOLD = timedelta(minutes=10)  # Time threshold for check-in status

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"

class DatabaseManager:
    @staticmethod
    def get_hosts():
        return supabase.table('settings').select('hostname, last_checked_in, check_in, timeout_interval').order('last_checked_in', desc=True).execute()

    @staticmethod
    def remove_host(hostname):
        return supabase.table('settings').delete().match({'hostname': hostname}).execute()

    @staticmethod
    def get_host_status(hostname):
        return supabase.table('settings').select('check_in').eq('hostname', hostname).execute()

    @staticmethod
    def get_local_user(hostname):
        return supabase.table('settings').select('localuser').eq('hostname', hostname).execute()

    @staticmethod
    def get_external_ip(hostname):
        return supabase.table("settings").select("external_ip").eq("hostname", hostname).execute()

    @staticmethod
    def update_sleep_interval(hostname, interval):
        return supabase.table("settings").update({"timeout_interval": interval}).eq("hostname", hostname).execute()

    @staticmethod
    def insert_command(agent_id, hostname, username, encrypted_command):
        return supabase.table('py2').insert({
            'agent_id': agent_id,
            'hostname': hostname,
            'username': username,
            'command': encrypted_command,
            'status': 'Pending'
        }).execute()

    @staticmethod
    def get_command_status(command_id):
        return supabase.table('py2').select('status', 'command', 'output', 'smbhost').eq('id', command_id).execute()

    @staticmethod
    def update_command_summary(command_id, encrypted_summary):
        return supabase.table('py2').update({'ai_summary': encrypted_summary}).eq('id', command_id).execute()

    @staticmethod
    def get_command_history(hostname, limit=50):
        return supabase.table('py2').select(
            'created_at', 'hostname', 'username', 'ip', 'command', 'output', 'smbhost', 'ai_summary'
        ).or_(
            f"hostname.eq.{hostname},smbhost.eq.{hostname}"
        ).order('created_at', desc=True).limit(limit).execute()

    @staticmethod
    def get_user(username):
        response = supabase.table('users').select('password_hash').eq('username', username).execute()
        return response.data  # This returns a list of matching users

    @staticmethod
    def insert_user(data):
        return supabase.table('users').insert(data).execute()

    @staticmethod
    def update_last_loggedin(username, timestamp):
        return supabase.table('users').update({'last_loggedin': timestamp}).eq('username', username).execute()

    @staticmethod
    def get_host_settings(hostname):
        response = supabase.table('settings').select('*').eq('hostname', hostname).execute()
        if response.data:
            return response.data[0]
        return None

    @staticmethod
    def upload_file(bucket_name, storage_path, file_object):
        return supabase.storage.from_(bucket_name).upload(storage_path, file_object)

    @staticmethod
    def insert_upload(data):
        return supabase.table('uploads').insert(data).execute()

    @staticmethod
    def get_downloads(hostname):
        return supabase.table('downloads').select('*').eq('hostname', hostname).eq('status', 'Completed').execute()

    @staticmethod
    def insert_download(data):
        return supabase.table('downloads').insert(data).execute()

    @staticmethod
    def update_download_status(download_id, status, file_url=None):
        update_data = {'status': status}
        if file_url:
            update_data['file_url'] = file_url
        return supabase.table('downloads').update(update_data).eq('id', download_id).execute()

    @staticmethod
    def get_auth_headers():
        return {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

db_manager = DatabaseManager()
