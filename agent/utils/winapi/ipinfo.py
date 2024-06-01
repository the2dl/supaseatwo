# utils/winapi/ipinfo.py

import ctypes
import socket
import struct

# Define the necessary constants and structures
MAX_ADAPTER_DESCRIPTION_LENGTH = 128
MAX_ADAPTER_NAME_LENGTH = 256
MAX_ADAPTER_ADDRESS_LENGTH = 8
MIB_IF_TYPE_OTHER = 1
MIB_IF_TYPE_ETHERNET = 6
MIB_IF_TYPE_TOKENRING = 9
MIB_IF_TYPE_FDDI = 15
MIB_IF_TYPE_PPP = 23
MIB_IF_TYPE_LOOPBACK = 24
MIB_IF_TYPE_SLIP = 28

class IP_ADDR_STRING(ctypes.Structure):
    pass

LP_IP_ADDR_STRING = ctypes.POINTER(IP_ADDR_STRING)

IP_ADDR_STRING._fields_ = [
    ("next", LP_IP_ADDR_STRING),
    ("ipAddress", ctypes.c_char * 16),
    ("ipMask", ctypes.c_char * 16),
    ("context", ctypes.c_ulong)
]

class IP_ADAPTER_INFO(ctypes.Structure):
    pass

LP_IP_ADAPTER_INFO = ctypes.POINTER(IP_ADAPTER_INFO)

IP_ADAPTER_INFO._fields_ = [
    ("next", LP_IP_ADAPTER_INFO),
    ("comboIndex", ctypes.c_ulong),
    ("adapterName", ctypes.c_char * MAX_ADAPTER_NAME_LENGTH + 4),
    ("description", ctypes.c_char * MAX_ADAPTER_DESCRIPTION_LENGTH + 4),
    ("addressLength", ctypes.c_uint),
    ("address", ctypes.c_ubyte * MAX_ADAPTER_ADDRESS_LENGTH),
    ("index", ctypes.c_ulong),
    ("type", ctypes.c_uint),
    ("dhcpEnabled", ctypes.c_uint),
    ("currentIpAddress", LP_IP_ADDR_STRING),
    ("ipAddressList", IP_ADDR_STRING),
    ("gatewayList", IP_ADDR_STRING),
    ("dhcpServer", IP_ADDR_STRING),
    ("haveWins", ctypes.c_uint),
    ("primaryWinsServer", IP_ADDR_STRING),
    ("secondaryWinsServer", IP_ADDR_STRING),
    ("leaseObtained", ctypes.c_ulong),
    ("leaseExpires", ctypes.c_ulong)
]

def get_ip_info():
    """Retrieve IP information using the Windows API."""
    GetAdaptersInfo = ctypes.windll.iphlpapi.GetAdaptersInfo
    GetAdaptersInfo.restype = ctypes.c_ulong
    GetAdaptersInfo.argtypes = [LP_IP_ADAPTER_INFO, ctypes.POINTER(ctypes.c_ulong)]

    adapter_list = (IP_ADAPTER_INFO * 16)()  # Allow space for 16 adapters
    buflen = ctypes.c_ulong(ctypes.sizeof(adapter_list))

    result = GetAdaptersInfo(ctypes.byref(adapter_list[0]), ctypes.byref(buflen))
    if result != 0:
        return f"Error: GetAdaptersInfo failed with error code {result}"

    ip_info = []

    for adapter in adapter_list:
        if not adapter.adapterName:
            break
        ip_info.append(f"Adapter Name: {adapter.adapterName.decode()}")
        ip_info.append(f"Description: {adapter.description.decode()}")
        ip_info.append(f"MAC Address: {'-'.join(f'{b:02X}' for b in adapter.address[:adapter.addressLength])}")
        ip_info.append(f"IP Address: {adapter.ipAddressList.ipAddress.decode()}")
        ip_info.append(f"IP Mask: {adapter.ipAddressList.ipMask.decode()}")
        ip_info.append(f"Gateway: {adapter.gatewayList.ipAddress.decode()}")
        ip_info.append("")

    return "\n".join(ip_info)
