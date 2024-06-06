import ctypes
import ctypes.wintypes as wintypes

# Constants
GENERIC_READ = 0x80000000
OPEN_EXISTING = 3
FILE_SHARE_READ = 0x00000001
INVALID_HANDLE_VALUE = -1

# Load the kernel32 DLL
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

def cat(file_path):
    """Read and output the contents of a file using Windows API."""
    
    # Open the file
    handle = kernel32.CreateFileW(
        file_path,
        GENERIC_READ,
        FILE_SHARE_READ,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    if handle == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        buffer_size = 4096
        buffer = ctypes.create_string_buffer(buffer_size)
        bytes_read = wintypes.DWORD(0)
        
        file_contents = []

        while True:
            success = kernel32.ReadFile(
                handle,
                buffer,
                buffer_size,
                ctypes.byref(bytes_read),
                None
            )
            if not success or bytes_read.value == 0:
                break
            file_contents.append(buffer.raw[:bytes_read.value].decode('utf-8', errors='ignore'))
        
        return ''.join(file_contents)

    finally:
        kernel32.CloseHandle(handle)
