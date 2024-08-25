# Active Directory Health Assessment Utility

This module provides a function to retrieve and assess the health of an Active Directory environment.

## Functions:
* `ad_health`: Retrieves users and groups from Active Directory and outputs the information to a JSON file.

## Usage:

ad_health <domain_controller.fqdn> <domain\username> <password> <output_file>


## Parameters:
* `domain_controller`: The FQDN or IP address of the domain controller to connect to.
* `domain\username`: The username (including domain) to authenticate with.
* `password`: The password for the specified user.
* `output_file`: The path where the JSON output file will be saved.

## Output:
The function generates a JSON file containing:
* List of users with their properties (username, display name, email, group memberships, creation date, last password set date)
* List of groups with their properties (name, description, members)

## Example:

ad_health dc01.example.com EXAMPLE\admin password123 C:\ad_health_report.json


## Note:
This command requires appropriate permissions to query Active Directory information. Ensure the provided user account has sufficient rights to perform LDAP queries on the domain controller.