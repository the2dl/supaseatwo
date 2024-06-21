import ctypes
from ctypes.wintypes import HANDLE, DWORD, BOOL, LPWSTR

# Constants
LOGON32_LOGON_NEW_CREDENTIALS = 9
LOGON32_PROVIDER_WINNT50 = 3

# Load DLLs
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

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

    # Ensure strings are properly encoded for use in LogonUserW
    username_buf = ctypes.create_unicode_buffer(username)
    password_buf = ctypes.create_unicode_buffer(password)
    domain_buf = ctypes.create_unicode_buffer(domain)

    if not advapi32.LogonUserW(username_buf, domain_buf, password_buf, LOGON32_LOGON_NEW_CREDENTIALS, LOGON32_PROVIDER_WINNT50, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())

    if not advapi32.ImpersonateLoggedOnUser(token):
        kernel32.CloseHandle(token)
        raise ctypes.WinError(ctypes.get_last_error())

    return "Token created and user impersonation started."

def revert_to_self():
    """Revert to the original security context."""
    if not advapi32.RevertToSelf():
        raise ctypes.WinError(ctypes.get_last_error())
    return "Reverted to self."
