from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateOptions, FileAttributes, ShareAccess, ImpersonationLevel, CreateDisposition, FilePipePrinterAccessMask
import os
import uuid
from time import sleep
from utils.retry_utils import with_retries

MAX_WRITE_SIZE = 8 * 1024 * 1024  # 8 MB
SUB_CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
WRITE_DELAY = 0.5  # Delay between writes in seconds
MAX_RETRIES = 5  # Maximum number of retries for credit errors
RETRY_DELAY = 30  # Delay between retries for credit errors in seconds

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

        # Read local file data and write in chunks
        with open(local_file_path, "rb") as f:
            offset = 0
            while True:
                chunk = f.read(MAX_WRITE_SIZE)
                if not chunk:
                    break

                chunk_offset = 0
                while chunk_offset < len(chunk):
                    sub_chunk = chunk[chunk_offset:chunk_offset + SUB_CHUNK_SIZE]
                    retries = 0
                    while retries < MAX_RETRIES:
                        try:
                            file_open.write(sub_chunk, offset + chunk_offset)
                            chunk_offset += len(sub_chunk)
                            sleep(WRITE_DELAY)  # Add delay between writes to handle credit issues
                            break
                        except Exception as e:
                            if "credits" in str(e).lower():
                                retries += 1
                                sleep(RETRY_DELAY)
                            else:
                                raise e
                    if retries == MAX_RETRIES:
                        raise Exception("Max retries reached for credit errors")

                offset += len(chunk)

        file_open.close()
        return f"Successfully wrote {local_file_path} to {remote_smb_path} on {server}"

    try:
        return with_retries(smb_write_operation)
    except Exception as e:
        return f"Error: {str(e)}"