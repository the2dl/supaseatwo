import win32api
import win32security

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
