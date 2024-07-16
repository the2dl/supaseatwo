# SupaSeaTwo

![seatwo](seatwo.png)

SupaSeaTwo is a Python application that facilitates interactions between a client and an agent via Supabase. It provides a robust interface for user authentication, file uploads/downloads, and command execution utilizing Supabase as the backend.

## Features

- **User Authentication:** Secure user login with bcrypt hashing.
- **File Uploads and Downloads:** Seamless upload and download of files via Supabase storage.
- **Command Execution:** Execute commands on the agent using native Windows API functions.
- **Shellcode Injection:** Execute shellcode from on-machine or in memory, both execute into explorer.exe.
- **Status Updates:** Real-time updates of agent status.

## Installation

Full installation docs can be found in [install](docs/install.md).

1. Clone the repository:
    ```sh
    git clone https://github.com/the2dl/supaseatwo.git
    cd supaseatwo
    ```

2. Install the required Python packages:

    - For Windows:
        ```sh
        pip install -r requirements-windows.txt
        ```

    - For Linux:
        ```sh
        pip install -r requirements-linux.txt
        ```

## Configuration

1. **Supabase Configuration:**
   - Sign up for a Supabase Free tier (unless you require more storage).
   - At this point you can run [sb_setup.sh](sb_setup.sh) to configure the supabase setup (Linux Supported) 
   - Set up your Supabase project and obtain the URL and API key from settings.
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase credentials.

2. **Supabase DB Setup:**

You can utilize the [supa.sql](supa.sql) file in this project to create your tables, pk's, and links.

Get your hostname, user, db and password from Project Settings > Database. Generate a new one if needed.

Sample:

`psql -h aws-0-us-east-1.yoursupabase.com -p 6543 -U postgres.projname postgres < supa.sql`

## Usage

### Python

You can run this via Python on the command line without compiling, compiling just gives you a binary to move around easier.

This has been tested with Python3.10 and Python3.11. Python3.12+ doesn't have support for pythonnet/etc as of 7/9/24.

### Client

The client script handles user authentication, file uploads, and command execution.

### Agent

The agent script provides utility functions for running commands, retrieving system information, and updating agent status.

## Compile Agent

```
pyinstaller --name supaseatwo --onefile --windowed --icon=seatwo.ico --add-data "utils;utils" supaseatwo.py
```

You may need to include a couple of dependencies, if so do this:

--add-data "\path\to\pywintypes310.dll;." --add-data "\path\to\win32timezone.py;."

## Pywine
If you want to compile from Linux cross-platform, pywine with the required imports is available. Install docker first on your base OS, adjust the pyinstaller packaging options as required.

```
cd pywine && docker build -t supaseatwo . && docker run --rm -v "$(pwd)":/app supaseatwo sh -c "wine pyinstaller --name supaseatwo --onefile --windowed --add-data '/app/utils;utils' /app/supaseatwo.py && cp -r /dist /app/dist"
```

This has gotten flagged by Defender AV every time. Compiling from a Windows device doesn't.

## PyQT

 cd into supaQT & run the below
 2511  python3 -m venv env\n
 2513  source env/bin/activate

pip install -r requirements.txt

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Unlicense License.
