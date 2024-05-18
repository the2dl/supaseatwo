import ctypes
import ctypes.wintypes as wintypes

# Define necessary constants
PROCESS_TERMINATE = 0x0001
CREATE_NEW_CONSOLE = 0x00000010
SW_HIDE = 0

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * wintypes.MAX_PATH),
    ]

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

def list_processes():
    """Lists all processes using Windows native APIs."""
    hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)

    processes = ["PID     PPID    Process Name"]
    processes.append("------  ------  ----------------")

    if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe32)):
        while ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe32)):
            processes.append(f"{pe32.th32ProcessID:<6}  {pe32.th32ParentProcessID:<6}  {pe32.szExeFile.decode()}")

    ctypes.windll.kernel32.CloseHandle(hSnapshot)
    return processes

def grep_processes(pattern):
    """Lists processes matching the given pattern."""
    all_processes = list_processes()
    filtered_processes = [all_processes[0], all_processes[1]]  # Keep the headers
    filtered_processes.extend([proc for proc in all_processes[2:] if pattern.lower() in proc.lower()])
    return filtered_processes

def terminate_process(process_id):
    """Terminates a process by its process ID."""
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, process_id)
    if not handle:
        error_code = ctypes.windll.kernel32.GetLastError()
        return f"Failed to open process with PID {process_id}. Error code: {error_code}"
    
    success = ctypes.windll.kernel32.TerminateProcess(handle, 0)
    if not success:
        error_code = ctypes.windll.kernel32.GetLastError()
        return f"Failed to terminate process with PID {process_id}. Error code: {error_code}"
    
    ctypes.windll.kernel32.CloseHandle(handle)
    return f"Process with PID {process_id} terminated successfully."

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
