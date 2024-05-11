import bcrypt
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = "https://aegfzwdrslyhgsugoecw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlZ2Z6d2Ryc2x5aGdzdWdvZWN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTI5NDM3MiwiZXhwIjoyMDMwODcwMzcyfQ.F_8dfPIk60brW4ZLXcBCph45KOe6jEUdSZHEikJuqhs"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user():
    username = input("Enter a username: ")
    password = input("Enter a password: ")

    # Hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    # Prepare user data
    data = {
        'username': username,
        'password_hash': hashed_password.decode()
    }

    try:
        supabase.table('users').insert(data).execute()
        print("User created successfully!")
    except Exception as e:
        print(f"Failed to create user: {e}")


if __name__ == "__main__":
    create_user()
