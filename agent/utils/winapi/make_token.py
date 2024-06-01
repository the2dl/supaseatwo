# utils/winapi/make_token.py

import ctypes
from ctypes.wintypes import HANDLE, DWORD, BOOL, LPWSTR

# Constants
LOGON32_LOGON_INTERACTIVE = 2
LOGON32_PROVIDER_DEFAULT = 0

# Load DLLs
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define necessary structures
class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", DWORD),
                ("Privileges", ctypes.c_ulonglong * 3)]

# Define necessary functions
advapi32.LogonUserW.restype = BOOL
advapi32.LogonUserW.argtypes = [LPWSTR, LPWSTR, LPWSTR, DWORD, DWORD, ctypes.POINTER(HANDLE)]

advapi32.ImpersonateLoggedOnUser.restype = BOOL
advapi32.ImpersonateLoggedOnUser.argtypes = [HANDLE]

advapi32.RevertToSelf.restype = BOOL

kernel32.CloseHandle.restype = BOOL
kernel32.CloseHandle.argtypes = [HANDLE]

def make_token(username, password, domain=''):
    """Create a new security token and impersonate the user."""
    token = HANDLE()

    if not advapi32.LogonUserW(username, domain, password, LOGON32_LOGON_INTERACTIVE, LOGON32_PROVIDER_DEFAULT, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())

    if not advapi32.ImpersonateLoggedOnUser(token):
        kernel32.CloseHandle(token)
        raise ctypes.WinError(ctypes.get_last_error())

    # Optionally return token for further use, or close handle if no longer needed
    return "Token created and user impersonation started."

def revert_to_self():
    """Revert to the original security context."""
    if not advapi32.RevertToSelf():
        raise ctypes.WinError(ctypes.get_last_error())
    return "Reverted to self."
