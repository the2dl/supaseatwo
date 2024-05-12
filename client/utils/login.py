import getpass
import bcrypt
from datetime import datetime

# Import color codes from commands module
from utils.commands import GREEN, RESET, RED
from .database import supabase

def login():
    username = input("Enter your username: ")
    user = supabase.table("users").select("password_hash").eq("username", username).execute().data

    if not user:
        print(f"{RED}Username not found. Would you like to register? (yes/no){RESET}")
        if input().strip().lower() == 'yes':
            return create_user(username)
        else:
            return None
    else:
        return authenticate_user(username)

def authenticate_user(username):
    password = getpass.getpass("Enter your password: ")
    user = supabase.table("users").select("password_hash").eq("username", username).execute().data
    stored_password_hash = user[0]['password_hash'].encode()
    if bcrypt.checkpw(password.encode(), stored_password_hash):
        print(f"{GREEN}Login successful{RESET}")
        update_last_loggedin(username)
        return username
    else:
        print(f"{RED}Invalid password.{RESET}")
        return None

def create_user(username):
    password = input("Enter a password: ")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    data = {
        'username': username,
        'password_hash': hashed_password.decode()
    }
    try:
        supabase.table('users').insert(data).execute()
        print(f"{GREEN}User created successfully!{RESET}")
        update_last_loggedin(username)
        return username
    except Exception as e:
        print(f"{RED}Failed to create user: {e}{RESET}")
        return None

def update_last_loggedin(username):
    current_time = datetime.utcnow()
    try:
        response = supabase.table("users").update({
            'last_loggedin': current_time.isoformat()
        }).eq('username', username).execute()
        if response.data:
            print(f"\n{GREEN}Welcome back {username}!{RESET}")
        else:
            print(f"{RED}Failed to update last login time. Error details: {response.text}{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred while updating last login time: {e}{RESET}")
