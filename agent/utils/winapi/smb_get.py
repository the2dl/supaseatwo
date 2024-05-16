from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateOptions, FileAttributes, ShareAccess, ImpersonationLevel, CreateDisposition, FilePipePrinterAccessMask
import os
import uuid
from utils.retry_utils import with_retries

def smb_get(remote_file_path, local_file_path, username=None, password=None, domain=None):
    """Gets a file from a remote host using the SMB protocol."""
    def smb_get_operation():
        # Parse the remote SMB path
        parts = remote_file_path.split("\\")
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
            desired_access=FilePipePrinterAccessMask.GENERIC_READ,
            create_disposition=CreateDisposition.FILE_OPEN,
            create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
            file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
            impersonation_level=ImpersonationLevel.Impersonation,
            share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE
        )

        # Read from remote file
        file_data = file_open.read(0, file_open.end_of_file)
        file_open.close()

        # Write local file data
        with open(local_file_path, "wb") as f:
            f.write(file_data)

        return f"Successfully downloaded {remote_file_path} to {local_file_path} from {server}"

    try:
        return with_retries(smb_get_operation)
    except Exception as e:
        return f"Error: {str(e)}"