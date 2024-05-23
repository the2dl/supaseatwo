# SupaSeaTwo

![seatwo](seatwo.png)

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
   - Sign up for a Supabase Free tier (unless you require more storage).
   - Set up your Supabase project and obtain the URL and API key from settings.
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase credentials.

2. **Supabase Tables:**
   - **Users Table:**
     ```sql
      CREATE SEQUENCE users_id_seq;
  
      CREATE TABLE users (
        id int4 PRIMARY KEY DEFAULT nextval('users_id_seq'),
        username varchar,
        password_hash varchar,
        last_loggedin timestamptz
      );
     ```

   - **Uploads Table:**
     ```sql
      CREATE TABLE uploads (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        hostname varchar,
        local_path text,
        remote_path text,
        file_url text,
        timestamp timestamptz DEFAULT now(),
        status varchar DEFAULT 'pending'::character varying,
        username text
      );
     ```

  - **Settings Table:**
     ```sql
      CREATE TABLE settings (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        hostname text,
        ip text,
        os text,
        timeout_interval int4 DEFAULT 30,
        check_in text DEFAULT 'Checked-in'::text,
        last_checked_in timestamp,
        username text
      );
     ```

  - **Downloads Table:**
     ```sql
      CREATE SEQUENCE downloads_id_seq;

      CREATE TABLE downloads (
        id int8 PRIMARY KEY DEFAULT nextval('downloads_id_seq'),
        hostname varchar,
        local_path text,
        remote_path text,
        file_url text,
        timestamp timestamptz DEFAULT now(),
        status varchar DEFAULT 'pending'::character varying,
        username text
      );
     ```

  - **Py2 Table:**
     ```sql
      CREATE TABLE py2 (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        created_at timestamptz DEFAULT now(),
        command text,
        status text DEFAULT 'Pending'::text,
        output text,
        hostname text,
        ip text,
        os text,
        timeout_interval int8 DEFAULT 30,
        username text
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
