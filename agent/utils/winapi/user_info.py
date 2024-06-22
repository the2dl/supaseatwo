import win32net
import win32netcon
from datetime import datetime, timedelta

def get_user_info(username, domain=None):
    try:
        user_info = win32net.NetUserGetInfo(domain, username, 3)
        user_info_11 = win32net.NetUserGetInfo(domain, username, 11)
        
        result = []
        result.append(f"User name                    {user_info['name']}")
        result.append(f"Full Name                    {user_info['full_name']}")
        result.append(f"Comment                      {user_info['comment']}")
        result.append(f"User's comment               {user_info['usr_comment']}")
        result.append(f"Country/region code          {user_info['country_code']}")
        result.append(f"Account active               {'Yes' if user_info['flags'] & win32netcon.UF_ACCOUNTDISABLE == 0 else 'No'}")
        result.append(f"Account expires              {format_account_expires(user_info['acct_expires'])}")
        
        result.append("\nPassword last set             (Not available through this API)")
        result.append(f"Password expires             {format_password_expires(user_info)}")
        result.append(f"Password changeable          (Not available through this API)")
        result.append(f"Password required            {'Yes' if user_info['flags'] & win32netcon.UF_PASSWD_NOTREQD == 0 else 'No'}")
        result.append(f"User may change password     {'Yes' if user_info['flags'] & win32netcon.UF_PASSWD_CANT_CHANGE == 0 else 'No'}")
        
        result.append(f"\nWorkstations allowed         {user_info['workstations'] if user_info['workstations'] else 'All'}")
        result.append(f"Logon script                 {user_info['script_path']}")
        result.append(f"User profile                 {user_info['profile']}")
        result.append(f"Home directory               {user_info['home_dir']}")
        result.append(f"Last logon                   {format_time(user_info_11.get('last_logon', 0))}")
        
        result.append("\nLogon hours allowed           All")
        
        # Get local group memberships
        local_groups = get_local_groups(username, domain)
        result.append("\nLocal Group Memberships       " + ", ".join(local_groups))
        
        # Get global group memberships
        global_groups = get_global_groups(username, domain)
        result.append("Global Group memberships      " + ", ".join(global_groups))
        
        return "\n".join(result)
        
    except win32net.error as e:
        return f"Error: {e}"

def get_local_groups(username, domain=None):
    try:
        groups = win32net.NetUserGetLocalGroups(domain, username)
        return [group if isinstance(group, str) else group['name'] for group in groups]
    except win32net.error:
        return ["Unable to retrieve local groups"]

def get_global_groups(username, domain=None):
    try:
        groups = win32net.NetUserGetGroups(domain, username)
        return [group[0] if isinstance(group, tuple) else group for group in groups]
    except win32net.error:
        return ["Unable to retrieve global groups"]

def format_time(time_value):
    if time_value == 0:
        return "Never"
    try:
        return (datetime(1970, 1, 1) + timedelta(seconds=time_value)).strftime("%m/%d/%Y %I:%M:%S %p")
    except (ValueError, OverflowError):
        return "Invalid timestamp"

def format_account_expires(time_value):
    if time_value == 0xFFFFFFFF or time_value == -1:
        return "Never"
    return format_time(time_value)

def format_password_expires(user_info):
    if user_info['flags'] & win32netcon.UF_DONT_EXPIRE_PASSWD:
        return "Never"
    elif 'password_age' in user_info and user_info['password_age'] != -1:
        max_age = user_info.get('max_passwd_age', 0)
        if max_age > 0:
            expires_in = max_age - user_info['password_age']
            if expires_in <= 0:
                return "Expired"
            else:
                return f"In {timedelta(seconds=expires_in)} days"
    return "Unable to determine"