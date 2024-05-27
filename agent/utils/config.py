import os
import requests
from supabase import create_client, Client

SUPABASE_URL = "https://aegfzwdrslyhgsugoecw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs"
DEFAULT_TIMEOUT = 30
DEFAULT_CHECK_IN = "Checked-in"
bucket_name = "files"
# Setup your pipes
PIPE_NAME_TEMPLATE = r'\\{ip_address}\pipe\wesleypipes'
PIPENAME = r'\\.\pipe\wesleypipes'

# Set the proxy environment variables
proxies = requests.utils.get_environ_proxies(os.environ.get('https_proxy') or os.environ.get('http_proxy'))
if proxies:
    os.environ['HTTP_PROXY'] = proxies.get('http')
    os.environ['HTTPS_PROXY'] = proxies.get('https')

# Create the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
