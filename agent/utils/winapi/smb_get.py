from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateOptions, FileAttributes, ShareAccess, ImpersonationLevel, CreateDisposition, FilePipePrinterAccessMask
import os
import uuid
from time import sleep
from utils.retry_utils import with_retries

MAX_READ_SIZE = 8 * 1024 * 1024  # 8 MB
SUB_CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
READ_DELAY = 0.5  # Delay between reads in seconds
MAX_RETRIES = 5  # Maximum number of retries for credit errors
RETRY_DELAY = 30  # Delay between retries for credit errors in seconds

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

        try:
            # Read from remote file and write to local file in chunks
            with open(local_file_path, "wb") as local_file:
                offset = 0
                while True:
                    try:
                        chunk = file_open.read(offset, SUB_CHUNK_SIZE)
                        if not chunk:
                            break
                        local_file.write(chunk)
                        local_file.flush()  # Ensure data is flushed to disk
                        os.fsync(local_file.fileno())  # Ensure data is physically written to disk
                        offset += len(chunk)
                        sleep(READ_DELAY)  # Add delay between reads to handle credit issues
                    except Exception as e:
                        if "credits" in str(e).lower():
                            sleep(RETRY_DELAY)
                        elif "STATUS_END_OF_FILE" in str(e) or "end-of-file marker" in str(e):
                            # End of file reached, stop reading
                            break
                        else:
                            raise e
        finally:
            file_open.close()

        return f"Successfully downloaded {remote_file_path} to {local_file_path} from {server}"

    try:
        result = with_retries(smb_get_operation)
        return result
    except Exception as e:
        return f"Error: {str(e)}"