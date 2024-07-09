## Detailed Installation Instructions

### Prerequisites

1. **Python**: Ensure that Python 3.x is installed on your system.
2. **Git**: Ensure that Git is installed to clone the repository.

### Windows Installation

1. **Install Python 3.10 or 3.11**
   - Download the latest version of Python from the official website: [Python Downloads](https://www.python.org/downloads/)
   - Run the installer and ensure to check the box that says "Add Python to PATH".

2. **Install Git**
   - Download Git from the official website: [Git Downloads](https://git-scm.com/download/win)
   - Run the installer with default settings.

3. **Clone the Repository**
   - Open Command Prompt or PowerShell.
   - Run the following command to clone the repository:
     ```sh
     git clone https://github.com/the2dl/supaseatwo.git
     cd supaseatwo
     ```

4. **Set Up a Virtual Environment**
   - Run the following commands to create and activate a virtual environment:
     ```sh
     python -m venv venv
     .\venv\Scripts\activate
     ```

5. **Install Dependencies**
   - Run the following command to install the required dependencies:
   Windows:
     ```sh
     pip install -r requirements-windows.txt
     ```

6. **Configure and signup for Supabase**
   - Signup for Supabase Free Tier
   - Optional: Setup custom domain to ensure supabase isn't blocked by default corporate proxy
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
     git clone https://github.com/the2dl/supaseatwo.git
     cd supaseatwo
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
   - Optional: Setup custom domain to ensure supabase isn't blocked by default corporate proxy
   - Update the configuration settings in `client/utils/database.py` and `agent/utils/config.py` with your Supabase URL and API key.

7. **Set Up Supabase Tables**
   - Log in to your Supabase dashboard.
   - Create the required tables using the provided SQL scripts in the documentation.

8. **Run the Application**
   - You can now run the client and agent scripts as needed.

### Supabase Table Setup

You can utilize the [supa.sql](supa.sql) file in this project to create your tables, pk's, and links.

### Running the Application

- **Client Side**:
  - Run the client script to handle user authentication, file uploads, and command execution.
    `python supaseaclient.py`

- **Agent Side**:
  - Run the agent script to provide utility functions for running commands, retrieving system information, and updating agent status.
    `python supaseatwo.py`

## Compile Agent (HTTPS and SMB)

```
pyinstaller --name supaseatwo --onefile --windowed --icon=seatwo.ico --add-data "utils;utils" supaseatwo.py
```
```
pyinstaller --name supaseatwo --onefile --windowed --icon=seatwo.ico --add-data "utils;utils" smb_agent.py
```