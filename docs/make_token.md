# Security Token Utility

This module provides functions to create a new security token and impersonate a user, as well as to revert to the original security context using Windows native APIs.

## Functions:
* `make_token`: Creates a new security token and impersonates the user.
* `revert_to_self`: Reverts to the original security context.