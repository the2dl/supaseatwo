# SupaSeaTwo

SupaSeaTwo is a Python application that facilitates interactions between a client and an agent via Supabase. It provides a robust interface for user authentication, file uploads/downloads, and command execution utilizing Supabase as the backend.

## Features

- **User Authentication:** Secure user login with bcrypt hashing.
- **File Uploads and Downloads:** Seamless upload and download of files via Supabase storage.
- **Command Execution:** Execute commands on the agent using native Windows API functions.
- **Status Updates:** Real-time updates of agent status.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/supaseatwo.git
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
   - Set up your Supabase project and obtain the URL and API key.
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase credentials.

2. **Supabase Tables:**
   - **Users Table:**
     ```sql
     CREATE TABLE users (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       username TEXT UNIQUE NOT NULL,
       password TEXT NOT NULL,
       last_login TIMESTAMP
     );
     ```

   - **Uploads Table:**
     ```sql
     CREATE TABLE uploads (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       file_name TEXT NOT NULL,
       file_url TEXT NOT NULL,
       status TEXT,
       created_at TIMESTAMP DEFAULT NOW()
     );
     ```

   - **Downloads Table:**
     ```sql
     CREATE TABLE downloads (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       file_name TEXT NOT NULL,
       file_url TEXT NOT NULL,
       status TEXT,
       created_at TIMESTAMP DEFAULT NOW()
     );
     ```

   - **Commands Table:**
     ```sql
     CREATE TABLE commands (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       command TEXT NOT NULL,
       result TEXT,
       status TEXT,
       created_at TIMESTAMP DEFAULT NOW()
     );
     ```

## Usage

### Client

The client script handles user authentication, file uploads, and command execution.

### Agent

The agent script provides utility functions for running commands, retrieving system information, and updating agent status.

## Compile Agent (fix later)

```
`C:\Users\dan\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\Scripts\pyinstaller --name supaseatwo --onefile --windowed --icon=seatwo.ico --add-data "utils;utils" --add-data "C:\\Users\\dan\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python310\\site-packages\\pywin32_system32\\pywintypes310.dll;." --add-data "C:\\Users\\dan\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python310\\site-packages\\win32\\lib\\win32timezone.py;." supaseatwo.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Unlicense License.
