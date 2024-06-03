import ctypes
import win32api
import win32net
import string

def get_drive_info():
    """Retrieves information about all the drives in the system."""
    try:
        drive_types = {
            0: "Unknown",
            1: "No Root Directory",
            2: "Removable Disk",
            3: "Local Disk",
            4: "Network Drive",
            5: "Compact Disc",
            6: "RAM Disk"
        }
        drives = []
        buffer = ctypes.create_string_buffer(254)
        ctypes.windll.kernel32.GetLogicalDriveStringsA(ctypes.sizeof(buffer), buffer)
        
        for drive in buffer.raw.split(b'\x00'):
            if drive:
                drive_letter = drive.decode('utf-8')
                drive_type = ctypes.windll.kernel32.GetDriveTypeA(drive)
                drive_type_str = drive_types.get(drive_type, 'Unknown')
                
                try:
                    vol_info = win32api.GetVolumeInformation(drive_letter)
                    vol_label = vol_info[0] if vol_info[0] else "No label"
                except win32api.error:
                    vol_label = "No label"

                if drive_type == 4:  # Network drive
                    net_name = ctypes.create_unicode_buffer(1024)
                    buffer_size = ctypes.c_ulong(1024)
                    result = ctypes.windll.mpr.WNetGetConnectionW(drive_letter[:2], net_name, ctypes.byref(buffer_size))
                    if result == 0:
                        net_path = net_name.value
                    else:
                        net_path = "Unknown"
                    drives.append(f"Drive: {drive_letter}, Type: {drive_type_str}, Label: {vol_label}, Network Path: {net_path}")
                else:
                    drives.append(f"Drive: {drive_letter}, Type: {drive_type_str}, Label: {vol_label}")
        
        return drives
    except Exception as e:
        return [f"Error: {str(e)}"]
