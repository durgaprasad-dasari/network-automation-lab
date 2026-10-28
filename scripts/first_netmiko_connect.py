"""First Netmiko connection: one read-only show command against the LAB router.

- Reads no passwords from this file. The password comes from the LAB_PASSWORD
  environment variable, or you are asked for it at the keyboard (hidden).
- Saves the real output to data/live_outputs/R1/ so you can compare it with the
  mock file in data/mock_outputs/R1/.
- Only run this against your own lab device.
"""
import getpass
import os
import sys
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

ROOT = Path(__file__).resolve().parent.parent
HOST = os.environ.get("LAB_HOST", "192.168.17.50")
USERNAME = os.environ.get("LAB_USERNAME", "netauto")
COMMAND = "show ip interface brief"


def get_password():
    """Use LAB_PASSWORD if set, otherwise ask without echoing what you type."""
    password = os.environ.get("LAB_PASSWORD")
    if not password:
        password = getpass.getpass(f"Lab password for {USERNAME}@{HOST}: ")
    return password


def find_down_interfaces(output):
    """Return interface names whose Protocol column (the last word) is 'down'."""
    down = []
    for line in output.splitlines()[1:]:  # skip the header line
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "down":
            down.append(parts[0])
    return down


def main():
    device = {
        "device_type": "cisco_ios",
        "host": HOST,
        "username": USERNAME,
        "password": get_password(),
    }
    try:
        with ConnectHandler(**device) as conn:
            prompt = conn.find_prompt()
            output = conn.send_command(COMMAND)
    except NetmikoAuthenticationException:
        print("Login failed: check the username and password.")
        return 1
    except NetmikoTimeoutException:
        print("Timed out: check the IP address, SSH settings, and network path.")
        return 1
    except Exception as exc:  # last resort so you always see a readable message
        print(f"Unexpected error: {type(exc).__name__}: {exc}")
        return 1

    print(f"Connected. Device prompt: {prompt}")
    print(f"--- {COMMAND} ---")
    print(output)

    down = find_down_interfaces(output)
    print(f"Interfaces with protocol down: {', '.join(down) if down else 'none'}")

    out_dir = ROOT / "data" / "live_outputs" / "R1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "show_ip_interface_brief.txt"
    out_file.write_text(output + "\n")
    print(f"Saved to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
