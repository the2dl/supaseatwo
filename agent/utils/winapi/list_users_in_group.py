import win32net

def list_users_in_group(group_name):
    """Lists all users in the specified group using Windows native APIs."""
    try:
        group_info = win32net.NetLocalGroupGetMembers(None, group_name, 1)
        users = [f"Users in group '{group_name}':"]
        for member in group_info[0]:
            users.append(member['name'])
        return users
    except Exception as e:
        return [f"Error: {str(e)}"]
