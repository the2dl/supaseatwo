import ctypes
import ctypes.wintypes as wintypes

# Define necessary constants
CREATE_NEW_CONSOLE = 0x00000010
SW_HIDE = 0

class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE)
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD)
    ]

def run_process(executable_path):
    """Launch a process using the Windows API."""
    startupinfo = STARTUPINFO()
    process_information = PROCESS_INFORMATION()

    startupinfo.cb = ctypes.sizeof(STARTUPINFO)
    startupinfo.dwFlags = 0x1
    startupinfo.wShowWindow = SW_HIDE

    success = ctypes.windll.kernel32.CreateProcessW(
        None, 
        executable_path, 
        None, 
        None, 
        False, 
        CREATE_NEW_CONSOLE, 
        None, 
        None, 
        ctypes.byref(startupinfo), 
        ctypes.byref(process_information)
    )

    if not success:
        error_code = ctypes.windll.kernel32.GetLastError()
        return f"Failed to launch process. Error code: {error_code}"
    else:
        return f"Process launched successfully with PID {process_information.dwProcessId}"
