from PyQt5.QtCore import QObject, pyqtSignal
import bcrypt
from datetime import datetime
from utils.database import db_manager

class LoginManager(QObject):
    login_success = pyqtSignal(str)
    login_failed = pyqtSignal(str)
    registration_success = pyqtSignal(str)
    registration_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def login(self, username, password):
        user_data = db_manager.get_user(username)

        if not user_data:
            self.login_failed.emit("Username not found.")
            return False

        # user_data is a list, so we need to access the first item
        user = user_data[0] if user_data else None
        if not user:
            self.login_failed.emit("Username not found.")
            return False

        stored_password_hash = user['password_hash'].encode()
        if bcrypt.checkpw(password.encode(), stored_password_hash):
            self.update_last_loggedin(username)
            self.login_success.emit(f"Welcome back {username}!")
            return True
        else:
            self.login_failed.emit("Invalid password.")
            return False

    def register(self, username, password):
        if db_manager.get_user(username):
            self.registration_failed.emit("Username already exists.")
            return False

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        data = {
            'username': username,
            'password_hash': hashed_password.decode()
        }
        try:
            db_manager.insert_user(data)
            self.update_last_loggedin(username)
            self.registration_success.emit(f"User {username} created successfully!")
            return True
        except Exception as e:
            self.registration_failed.emit(f"Failed to create user: {e}")
            return False

    def update_last_loggedin(self, username):
        current_time = datetime.utcnow()
        try:
            db_manager.update_last_loggedin(username, current_time.isoformat())
        except Exception as e:
            print(f"An error occurred while updating last login time: {e}")

login_manager = LoginManager()
