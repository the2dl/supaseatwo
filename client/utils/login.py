import getpass
import bcrypt
from datetime import datetime

# Import color codes from commands module
from utils.commands import GREEN, RESET
from .database import supabase

# Import the Supabase client from the database module within the utils package
from .database import supabase

def login():
    """Prompts the user forcredentials and checks them against the database."""

    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    # Fetch the stored hashed password for the given username
    user = supabase.table("users").select("password_hash").eq("username", username).execute().data

    if not user:
        print(f"{RED}Invalid username.{RESET}")  # Indicate error with colored output
        return None

    # Compare entered password with stored hash using bcrypt
    stored_password_hash = user[0]['password_hash'].encode()
    if bcrypt.checkpw(password.encode(), stored_password_hash):
        print(f"{GREEN}Login successful{RESET}")
        update_last_loggedin(username)  # Update the login timestamp
        return username
    else:
        print(f"{RED}Invalid password.{RESET}")
        return None


def update_last_loggedin(username):
    """Updates the last logged-in timestamp for the given user in the database."""

    current_time = datetime.utcnow()

    try:
        response = supabase.table("users").update({
            'last_loggedin': current_time.isoformat()
        }).eq('username', username).execute()

        if response.data:
            print(f"\nWelcome back {username}!")

        else:
            print(f"Failed to update last login time. Error details: {response.text}")

    except Exception as e:
        print(f"An error occurred while updating last login time: {e}")
