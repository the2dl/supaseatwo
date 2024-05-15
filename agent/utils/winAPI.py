import os
import win32file
import win32api
import win32security
import win32net
from datetime import datetime

def get_file_attributes_string(file_attributes):
    """Convert file attributes to a string representing the mode."""
    attributes = [
        ('d', win32file.FILE_ATTRIBUTE_DIRECTORY),
        ('r', win32file.FILE_ATTRIBUTE_READONLY),
        ('h', win32file.FILE_ATTRIBUTE_HIDDEN),
        ('s', win32file.FILE_ATTRIBUTE_SYSTEM),
        ('a', win32file.FILE_ATTRIBUTE_ARCHIVE)
    ]
    mode = ''.join(attr if (file_attributes & flag) else '-' for attr, flag in attributes)
    return mode

def format_file_info(file_info):
    """Format file information into a readable string."""
    mode = get_file_attributes_string(file_info[0])
    last_write_time = file_info[3]  # This is already a pywintypes.datetime object
    if last_write_time:
        last_write_time_str = last_write_time.strftime('%m/%d/%Y %I:%M %p')
    else:
        last_write_time_str = 'Unknown'

    length = file_info[5] if mode[0] != 'd' else 0  # Directories have a length of 0
    name = file_info[8]
    return f"{mode:<10} {last_write_time_str:<22} {length:<12} {name}"

def wls(path):
    """Lists all files and directories at the given path using Windows native APIs."""
    files = ["Permissions  Last Write Time       Size       Name"]
    files.append("-----------  -------------------  ---------- ----------------------------------")
    try:
        # Normalize the path to ensure compatibility with FindFilesW
        normalized_path = os.path.normpath(path)
        if not os.path.isdir(normalized_path):
            raise ValueError(f"The path '{normalized_path}' is not a valid directory.")

        # Ensure path is a directory
        handle = win32file.FindFilesW(normalized_path + '\\*')

        for file in handle:
            files.append(format_file_info(file))
    except Exception as e:
        files = ["Error: " + str(e)]

    return files

def wami():
    """Retrieves the username of the current user and their associated information using Windows native APIs."""
    try:
        username = win32api.GetUserName()
        user_info = [f"Username: {username}"]

        # Get the current user's token
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)

        # Get user SID
        user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        user_info.append(f"User SID: {win32security.ConvertSidToStringSid(user_sid)}")

        # Get user groups
        groups = win32security.GetTokenInformation(token, win32security.TokenGroups)
        group_info = []
        for group in groups:
            sid = group[0]
            attributes = group[1]
            group_name, _, _ = win32security.LookupAccountSid(None, sid)
            attr_str = []
            if attributes & win32security.SE_GROUP_ENABLED:
                attr_str.append("Enabled")
            if attributes & win32security.SE_GROUP_USE_FOR_DENY_ONLY:
                attr_str.append("Use for deny only")
            group_info.append(f"{group_name} ({win32security.ConvertSidToStringSid(sid)}): {', '.join(attr_str)}")
        user_info.append("Groups:")
        user_info.extend(group_info)

        # Get user privileges
        privileges = win32security.GetTokenInformation(token, win32security.TokenPrivileges)
        privilege_info = []
        for priv in privileges:
            luid = priv[0]
            attributes = priv[1]
            priv_name = win32security.LookupPrivilegeName(None, luid)
            attr_str = []
            if attributes & win32security.SE_PRIVILEGE_ENABLED:
                attr_str.append("Enabled")
            if attributes & win32security.SE_PRIVILEGE_ENABLED_BY_DEFAULT:
                attr_str.append("Enabled by default")
            if attributes & win32security.SE_PRIVILEGE_REMOVED:
                attr_str.append("Removed")
            privilege_info.append(f"{priv_name}: {', '.join(attr_str)}")
        user_info.append("Privileges:")
        user_info.extend(privilege_info)

        return user_info
    except Exception as e:
        return [f"Error: {str(e)}"]

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
