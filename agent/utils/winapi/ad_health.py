from ldap3 import Server, Connection, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES
import json
from utils.retry_utils import with_retries
import logging
from datetime import datetime, timedelta, timezone

def ad_health(domain_controller, username, password, output_file):
    """Retrieves users and groups from Active Directory and outputs to JSON."""
    def ad_health_operation():
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)

        # Connect to the domain controller
        server = Server(domain_controller, get_info=ALL)
        conn = Connection(server, user=username, password=password, authentication=NTLM)
        
        if not conn.bind():
            raise Exception(f"Failed to bind to {domain_controller}: {conn.result}")

        logger.debug(f"Successfully bound to {domain_controller}")

        # Get the domain base DN
        domain_base_dn = server.info.other['defaultNamingContext'][0]
        logger.debug(f"Domain Base DN: {domain_base_dn}")

        # Open the output file in write mode and start the JSON array
        with open(output_file, 'w') as f:
            f.write('{"users": [\n')

        # Search for users with paged search
        user_search_filter = '(&(objectClass=user)(objectCategory=person))'
        logger.debug(f"Searching for users with filter: {user_search_filter}")
        page_size = 1000
        cookie = None
        first_entry = True

        while True:
            conn.search(search_base=domain_base_dn,
                        search_filter=user_search_filter,
                        search_scope=SUBTREE,
                        attributes=['sAMAccountName', 'displayName', 'mail', 'memberOf', 'whenCreated', 'pwdLastSet'],
                        paged_size=page_size,
                        paged_cookie=cookie)
            
            for entry in conn.entries:
                # Convert whenCreated to ISO format
                when_created = entry.whenCreated.value
                when_created_iso = when_created.isoformat() if when_created else None

                # Convert pwdLastSet to ISO format
                pwd_last_set = entry.pwdLastSet.value
                if pwd_last_set:
                    if isinstance(pwd_last_set, datetime):
                        pwd_last_set_iso = pwd_last_set.isoformat()
                    elif isinstance(pwd_last_set, int) and pwd_last_set != 0:
                        pwd_last_set_datetime = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=pwd_last_set // 10)
                        pwd_last_set_iso = pwd_last_set_datetime.isoformat()
                    else:
                        pwd_last_set_iso = None
                else:
                    pwd_last_set_iso = None

                user = {
                    'username': entry.sAMAccountName.value,
                    'display_name': entry.displayName.value,
                    'email': entry.mail.value,
                    'groups': [str(group) for group in entry.memberOf],
                    'created_date': when_created_iso,
                    'password_last_set': pwd_last_set_iso
                }

                # Write user to file
                with open(output_file, 'a') as f:
                    if not first_entry:
                        f.write(',\n')
                    json.dump(user, f, indent=2)
                    first_entry = False

            cookie = conn.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            if not cookie:
                break

        # Close the JSON array for users
        with open(output_file, 'a') as f:
            f.write('\n],\n"groups": [\n')

        # Search for groups with paged search
        group_search_filter = '(objectClass=group)'
        logger.debug(f"Searching for groups with filter: {group_search_filter}")
        cookie = None
        first_entry = True

        while True:
            conn.search(search_base=domain_base_dn,
                        search_filter=group_search_filter,
                        search_scope=SUBTREE,
                        attributes=['sAMAccountName', 'description', 'member'],
                        paged_size=page_size,
                        paged_cookie=cookie)
            
            for entry in conn.entries:
                group = {
                    'name': entry.sAMAccountName.value,
                    'description': entry.description.value,
                    'members': [str(member) for member in entry.member]
                }

                # Write group to file
                with open(output_file, 'a') as f:
                    if not first_entry:
                        f.write(',\n')
                    json.dump(group, f, indent=2)
                    first_entry = False

            cookie = conn.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            if not cookie:
                break

        # Close the JSON array for groups and the JSON object
        with open(output_file, 'a') as f:
            f.write('\n]\n}')

        conn.unbind()
        return f"Successfully retrieved AD information and wrote it to {output_file}. Users: {len(conn.entries)}, Groups: {len(conn.entries)}"

    try:
        return with_retries(ad_health_operation)
    except Exception as e:
        logging.error(f"Error in ad_health: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

def handle_ad_health_command(command_parts):
    """Handles the ad_health command from the agent."""
    if len(command_parts) != 5:
        return "Error: Invalid command format. Use 'ad_health <domain_controller> <domain\\username> <password> <output_file>'"
    
    _, domain_controller, username, password, output_file = command_parts
    return ad_health(domain_controller, username, password, output_file)