# utils/winapi/ipinfo.py

import ctypes
from ctypes import wintypes

MAX_ADAPTER_NAME_LENGTH = 256
MAX_ADAPTER_ADDRESS_LENGTH = 8
MAX_ADAPTER_DESCRIPTION_LENGTH = 128

# Define necessary structures
class IP_ADDR_STRING(ctypes.Structure):
    pass

IP_ADDR_STRING._fields_ = [
    ("Next", ctypes.POINTER(IP_ADDR_STRING)),
    ("IpAddress", wintypes.CHAR * 16),
    ("IpMask", wintypes.CHAR * 16),
    ("Context", wintypes.DWORD)
]

class IP_ADAPTER_INFO(ctypes.Structure):
    pass

IP_ADAPTER_INFO._fields_ = [
    ("Next", ctypes.POINTER(IP_ADAPTER_INFO)),
    ("ComboIndex", wintypes.DWORD),
    ("AdapterName", wintypes.CHAR * (MAX_ADAPTER_NAME_LENGTH + 4)),
    ("Description", wintypes.CHAR * (MAX_ADAPTER_DESCRIPTION_LENGTH + 4)),
    ("AddressLength", wintypes.UINT),
    ("Address", wintypes.BYTE * MAX_ADAPTER_ADDRESS_LENGTH),
    ("Index", wintypes.DWORD),
    ("Type", wintypes.UINT),
    ("DhcpEnabled", wintypes.UINT),
    ("CurrentIpAddress", ctypes.POINTER(IP_ADDR_STRING)),
    ("IpAddressList", IP_ADDR_STRING),
    ("GatewayList", IP_ADDR_STRING),
    ("DhcpServer", IP_ADDR_STRING),
    ("HaveWins", wintypes.BOOL),
    ("PrimaryWinsServer", IP_ADDR_STRING),
    ("SecondaryWinsServer", IP_ADDR_STRING),
    ("LeaseObtained", wintypes.ULONG),
    ("LeaseExpires", wintypes.ULONG)
]

# Load necessary DLLs
iphlpapi = ctypes.WinDLL('iphlpapi.dll')

def get_ip_info():
    """Retrieve IP configuration information."""
    adapter_info_size = wintypes.ULONG()
    iphlpapi.GetAdaptersInfo(None, ctypes.byref(adapter_info_size))

    adapter_info = ctypes.create_string_buffer(adapter_info_size.value)
    iphlpapi.GetAdaptersInfo(ctypes.byref(adapter_info), ctypes.byref(adapter_info_size))

    adapter = ctypes.cast(adapter_info, ctypes.POINTER(IP_ADAPTER_INFO)).contents

    info = []
    while True:
        info.append({
            'AdapterName': adapter.AdapterName.decode(),
            'Description': adapter.Description.decode(),
            'IpAddress': adapter.IpAddressList.IpAddress.decode(),
            'IpMask': adapter.IpAddressList.IpMask.decode(),
            'Gateway': adapter.GatewayList.IpAddress.decode(),
            'DhcpServer': adapter.DhcpServer.IpAddress.decode(),
            'HaveWins': adapter.HaveWins,
            'PrimaryWinsServer': adapter.PrimaryWinsServer.IpAddress.decode(),
            'SecondaryWinsServer': adapter.SecondaryWinsServer.IpAddress.decode(),
        })
        if not adapter.Next:
            break
        adapter = adapter.Next.contents

    return info
