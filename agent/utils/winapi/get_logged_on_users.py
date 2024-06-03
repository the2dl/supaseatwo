import win32net

def get_logged_on_users():
    """Retrieves the list of users currently logged on to the system."""
    try:
        resume_handle = 0
        logged_on_users = []
        
        while True:
            users, total, resume_handle = win32net.NetWkstaUserEnum(None, 1, resume_handle)
            for user in users:
                logged_on_users.append(user['username'])
            if resume_handle == 0:
                break
        
        return logged_on_users
    except Exception as e:
        return [f"Error: {str(e)}"]
