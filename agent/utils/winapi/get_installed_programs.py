import winreg

def get_installed_programs():
    """Retrieves the list of installed programs on the system."""
    try:
        uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key)
        programs = []

        for i in range(0, winreg.QueryInfoKey(hkey)[0]):
            sub_key_name = winreg.EnumKey(hkey, i)
            sub_key = winreg.OpenKey(hkey, sub_key_name)
            try:
                program_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                programs.append(program_name)
            except FileNotFoundError:
                continue

        return programs
    except Exception as e:
        return [f"Error: {str(e)}"]
