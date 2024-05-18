import ctypes
import ctypes.wintypes as wintypes

# Define necessary constants
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

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