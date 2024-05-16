from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateOptions, FileAttributes, ShareAccess, ImpersonationLevel, CreateDisposition, FilePipePrinterAccessMask
import os
import uuid
from utils.retry_utils import with_retries

def smb_write(local_file_path, remote_smb_path, username=None, password=None, domain=None):
    """Writes a file to a remote host using the SMB protocol."""
    def smb_write_operation():
        # Parse the remote SMB path
        parts = remote_smb_path.split("\\")
        server = parts[2]
        share_name = parts[3]
        remote_path = "\\".join(parts[4:])

        # Establish connection and session
        connection = Connection(uuid.uuid4(), server, 445)
        connection.connect()
        session = Session(connection, username, password, domain)
        session.connect()

        # Connect to the share
        tree = TreeConnect(session, f"\\\\{server}\\{share_name}")
        tree.connect()

        # Open the remote file
        file_open = Open(tree, remote_path)
        file_open.create(
            desired_access=FilePipePrinterAccessMask.GENERIC_WRITE,
            create_disposition=CreateDisposition.FILE_OVERWRITE_IF,
            create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
            file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
            impersonation_level=ImpersonationLevel.Impersonation,
            share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE
        )

        # Read local file data
        with open(local_file_path, "rb") as f:
            file_data = f.read()

        # Write to remote file
        file_open.write(file_data, 0)
        file_open.close()

        return f"Successfully wrote {local_file_path} to {remote_smb_path} on {server}"

    try:
        return with_retries(smb_write_operation)
    except Exception as e:
        return f"Error: {str(e)}"