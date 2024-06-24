from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta
from utils.database import supabase, db_manager
from utils.encryption_utils import fetch_agent_info_by_hostname

class HostManager(QObject):
    hosts_updated = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.CHECK_IN_THRESHOLD = timedelta(minutes=10)
        self.DEFAULT_TIMEOUT = 600

    def get_hosts(self):
        response = supabase.table('settings').select('hostname, last_checked_in, check_in, timeout_interval').order('last_checked_in', desc=True).execute()
        hosts = response.data
        now = datetime.utcnow()

        formatted_hosts = []
        for host in hosts:
            hostname = host['hostname']
            last_checked_in_str = host.get('last_checked_in')
            current_check_in_status = host.get('check_in', 'Unknown')
            timeout_interval = host.get('timeout_interval', self.DEFAULT_TIMEOUT)

            if current_check_in_status == "Dead":
                status = "dead"
            elif last_checked_in_str:
                last_checked_in = datetime.fromisoformat(last_checked_in_str[:-1])
                time_difference = now - last_checked_in
                if time_difference > self.CHECK_IN_THRESHOLD and timeout_interval <= self.CHECK_IN_THRESHOLD.total_seconds():
                    status = "likely dead"
                else:
                    status = "alive"
            else:
                status = "no check-in info" if current_check_in_status == 'Unknown' else current_check_in_status

            formatted_hosts.append({
                'hostname': hostname,
                'status': status,
                'last_checked_in': last_checked_in_str,
                'timeout_interval': timeout_interval
            })

        self.hosts_updated.emit(formatted_hosts)
        return formatted_hosts

    def remove_host(self, hostname):
        try:
            response = supabase.table('settings').delete().match({'hostname': hostname}).execute()
            if response.data:
                self.get_hosts()  # Refresh the host list
                return True
            else:
                print(f"Failed to remove host: {hostname}")
                return False
        except Exception as e:
            print(f"An error occurred while removing host {hostname}: {e}")
            return False

    def get_host_status(self, hostname):
        response = supabase.table('settings').select('check_in').eq('hostname', hostname).execute()
        if response.data:
            return response.data[0]['check_in']
        return 'Unknown'

    def get_local_user(self, hostname):
        response = supabase.table('settings').select('localuser').eq('hostname', hostname).execute()
        if response.data:
            return response.data[0].get('localuser')
        return None

    def get_external_ip(self, hostname):
        response = supabase.table("settings").select("external_ip").eq("hostname", hostname).execute()
        if response.data:
            return response.data[0].get('external_ip', 'unknown')
        return 'unknown'

    def get_agent_info(self, hostname):
        response = db_manager.get_host_settings(hostname)
        if response:
            return response.get('agent_id'), response.get('encryption_key')
        return None, None

    def update_sleep_interval(self, hostname, interval):
        try:
            supabase.table("settings").update({
                "timeout_interval": interval
            }).eq("hostname", hostname).execute()
            return True
        except Exception as e:
            print(f"Failed to update sleep interval for {hostname}: {e}")
            return False
