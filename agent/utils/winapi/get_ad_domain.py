import win32security

def get_ad_domain():
    """Retrieves the Active Directory domain name using Windows native APIs."""
    try:
        # Get the domain controller info
        domain_controller_info = win32security.DsGetDcName()
        domain_name = domain_controller_info['DomainName']
        return domain_name
    except Exception as e:
        return f"Error: {str(e)}"
