import subprocess

def scan_networks():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"])
        ssids = set(line.strip() for line in result.decode().split('\n') if line.strip())
        return list(ssids)
    except Exception as e:
        print(f"[ERROR] Wi-Fi scan failed: {e}")
        return []

def connect_to_wifi(ssid, password):
    try:
        subprocess.run([
            "nmcli", "dev", "wifi", "connect", ssid, "password", password
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to connect to {ssid}: {e}")
        return False

def is_wifi_connected():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "STATE", "g"])
        state = result.decode().strip()
        return state == "connected"
    except Exception:
        return False
