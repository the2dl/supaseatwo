from supabase import create_client, Client
from datetime import datetime, timedelta

# Supabase configuration (Replace with your actual values)
SUPABASE_URL = "https://aegfzwdrslyhgsugoecw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs"
OPENAI_API_KEY = "sk-proj-LQ5dm3iwTPD8Gkg3ys0ET3BlbkFJYrX98APv3iBjcHHRUNEU"

# Create a Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHECK_IN_THRESHOLD = timedelta(minutes=10)  # Time threshold for check-in status

def get_public_url(bucket_name, file_path):
    """Constructs the public URL for a file in Supabase storage."""
    return f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/{bucket_name}/{file_path}"
