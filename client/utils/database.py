from supabase import create_client, Client
from datetime import datetime, timedelta

# Supabase configuration (Replace with your actual values)
SUPABASE_URL = "https://blahoecw.supabase.co"
SUPABASE_KEY = "your_supabase_key"
OPENAI_API_KEY = "your_oai_key"

# Create a Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHECK_IN_THRESHOLD = timedelta(minutes=10)  # Time threshold for check-in status

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"

def get_setting(key):
    """Fetches a setting value from the settings table in Supabase."""
    response = supabase.table('settings').select(key).execute()
    if response.data and key in response.data[0]:
        return response.data[0][key]
    return None
