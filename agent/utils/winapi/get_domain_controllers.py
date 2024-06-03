import win32security
import win32net

def get_domain_controllers():
    """Retrieves the list of domain controllers using Windows native APIs."""
    try:
        # Get the primary domain name
        domain_info = win32net.NetWkstaGetInfo(None, 100)
        domain_name = domain_info['langroup']
        
        # Retrieve domain controller information
        dc_info = win32security.DsGetDcName(None, domain_name)
        domain_controller_name = dc_info['DomainControllerName']
        
        return [domain_controller_name]
    except Exception as e:
        return [f"Error: {str(e)}"]
