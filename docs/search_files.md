Certainly! Here is the updated documentation for the new file search functionality:

# File Search Utility

This module provides functions to search local user directories, ProgramData, and other interesting areas for files with sensitive information.

## Functions:
* `search_files`: Searches for files with specific keywords in their names and checks for the presence of AWS, GCP, and Azure credential files.
* `search`: Aggregates the search results and formats them for output.

## Key Features:
* Searches for files with keywords like "password", "credential", "secret", etc.
* Looks for specific cloud provider credential files (AWS, GCP, Azure)
* Searches in multiple directories including user home directories, ProgramData, and temporary directories
* Unique result aggregation to avoid duplicates
* Direct file path search for common cloud credential storage locations

## Usage:
The search process runs synchronously and provides a list of files found with sensitive information, allowing the agent to act on this data immediately.