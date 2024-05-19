## Detailed Installation Instructions

### Prerequisites

1. **Python**: Ensure that Python 3.x is installed on your system.
2. **Git**: Ensure that Git is installed to clone the repository.

### Windows Installation

1. **Install Python 3.x**
   - Download the latest version of Python from the official website: [Python Downloads](https://www.python.org/downloads/)
   - Run the installer and ensure to check the box that says "Add Python to PATH".

2. **Install Git**
   - Download Git from the official website: [Git Downloads](https://git-scm.com/download/win)
   - Run the installer with default settings.

3. **Clone the Repository**
   - Open Command Prompt or PowerShell.
   - Run the following command to clone the repository:
     ```sh
     git clone https://github.com/yourusername/boac2.git
     cd boac2
     ```

4. **Set Up a Virtual Environment**
   - Run the following commands to create and activate a virtual environment:
     ```sh
     python -m venv venv
     .\venv\Scripts\activate
     ```

5. **Install Dependencies**
   - Run the following command to install the required dependencies:
     ```sh
     pip install -r requirements-windows.txt
     ```

6. **Configure and signup for Supabase**
   - Signup for Supabase Free Tier
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase URL and API key.

7. **Set Up Supabase Tables**
   - Log in to your Supabase dashboard.
   - Create the required tables using the provided SQL scripts in the documentation.

8. **Run the Application**
   - You can now run the client and agent scripts as needed.

### Linux Installation

1. **Install Python 3.x**
   - Most Linux distributions come with Python pre-installed. If not, install Python using the package manager:
     ```sh
     sudo apt update
     sudo apt install python3 python3-venv python3-pip
     ```

2. **Install Git**
   - Install Git using the package manager:
     ```sh
     sudo apt install git
     ```

3. **Clone the Repository**
   - Open a terminal.
   - Run the following command to clone the repository:
     ```sh
     git clone https://github.com/yourusername/boac2.git
     cd boac2
     ```

4. **Set Up a Virtual Environment**
   - Run the following commands to create and activate a virtual environment:
     ```sh
     python3 -m venv venv
     source venv/bin/activate
     ```

5. **Install Dependencies**
   - Run the following command to install the required dependencies:
     ```sh
     pip install -r requirements-linux.txt
     ```

6. **Configure and signup for Supabase**
   - Signup for Supabase Free Tier
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase URL and API key.

7. **Set Up Supabase Tables**
   - Log in to your Supabase dashboard.
   - Create the required tables using the provided SQL scripts in the documentation.

8. **Run the Application**
   - You can now run the client and agent scripts as needed.

### Supabase Table Setup

Create the following tables in your Supabase project using the SQL scripts provided:

#### Users Table
```sql
CREATE SEQUENCE users_id_seq;

CREATE TABLE users (
    id int4 PRIMARY KEY DEFAULT nextval('users_id_seq'),
    username varchar,
    password_hash varchar,
    last_loggedin timestamptz
);
```

#### Uploads Table
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

#### Downloads Table
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

#### Settings Table
```sql
CREATE TABLE settings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    hostname text,
    ip text,
    os text,
    timeout_interv int4 DEFAULT 30,
    check_in text DEFAULT 'Checked-in'::text,
    last_checked_in timestamp,
    username text
);
```

### Running the Application

- **Client Side**:
  - Run the client script to handle user authentication, file uploads, and command execution.
    `python supaseaclient.py`

- **Agent Side**:
  - Run the agent script to provide utility functions for running commands, retrieving system information, and updating agent status.
    `python supaseatwo.py`