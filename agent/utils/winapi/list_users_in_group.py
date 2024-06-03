import win32net

def list_users_in_group(group_type, group_name):
    """Lists all users in the specified group (local or domain) using Windows native APIs."""
    try:
        if group_type.lower() == 'local':
            group_info = win32net.NetLocalGroupGetMembers(None, group_name, 1)
            users = [f"Users in local group '{group_name}':"]
            for member in group_info[0]:
                users.append(member['name'])
        elif group_type.lower() == 'dom':
            domain_name, group_name = group_name.split("\\", 1)
            group_info = win32net.NetGroupGetUsers(domain_name, group_name, 1)
            users = [f"Users in domain group '{domain_name}\\{group_name}':"]
            for member in group_info[0]:
                users.append(member['name'])
        else:
            return [f"Error: Invalid group type '{group_type}'. Use 'local' or 'dom'."]
        return users
    except ValueError:
        return [f"Error: Incorrect format for domain group name. It should be in the format 'domain\\group_name'."]
    except Exception as e:
        return [f"Error: {str(e)}"]
