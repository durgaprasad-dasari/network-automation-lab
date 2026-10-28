"""Run one read-only show command on every device in data/inventory.csv.

For each device it:
  1. validates the IP address,
  2. connects over SSH with Netmiko,
  3. runs 'show ip interface brief',
  4. saves the raw output to data/live_outputs/<hostname>/,
and at the end it prints a summary and saves a timestamped CSV report in reports/.

One device failing never stops the others. Only run this against LAB devices.
The password is never stored in this file: set LAB_PASSWORD or type it when asked.
"""
import csv
import getpass
import ipaddress
import os
import sys
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "data" / "inventory.csv"
USERNAME = os.environ.get("LAB_USERNAME", "netauto")
COMMAND = "show ip interface brief"


def get_password():
    """Use LAB_PASSWORD if set, otherwise ask without echoing what you type."""
    password = os.environ.get("LAB_PASSWORD")
    if not password:
        password = getpass.getpass(f"Lab password for user '{USERNAME}': ")
    return password


def load_inventory(path):
    """Read the inventory CSV and return a list of dictionaries (one per device)."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def find_down_interfaces(output):
    """Return interface names whose Protocol column (the last word) is 'down'."""
    down = []
    for line in output.splitlines()[1:]:  # skip the header line
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "down":
            down.append(parts[0])
    return down


def collect(device, password):
    """Connect to one device. Return (status, detail, output)."""
    try:
        ipaddress.IPv4Address(device["ip"])
    except ipaddress.AddressValueError:
        return "SKIPPED", f"invalid IP address '{device['ip']}'", ""

    params = {
        "device_type": device["device_type"],
        "host": device["ip"],
        "username": USERNAME,
        "password": password,
        "conn_timeout": 10,
    }
    try:
        with ConnectHandler(**params) as conn:
            output = conn.send_command(COMMAND)
    except NetmikoAuthenticationException:
        return "FAILED", "authentication failed", ""
    except NetmikoTimeoutException:
        return "FAILED", "timed out (unreachable or SSH not enabled)", ""
    except Exception as exc:  # keep going with the next device
        return "FAILED", f"{type(exc).__name__}: {exc}", ""

    down = find_down_interfaces(output)
    detail = "down: " + ", ".join(down) if down else "no down interfaces"
    return "OK", detail, output


def save_output(hostname, output):
    out_dir = ROOT / "data" / "live_outputs" / hostname
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "show_ip_interface_brief.txt"
    out_file.write_text(output + "\n")
    return out_file


def main():
    devices = load_inventory(INVENTORY)
    password = get_password()
    results = []

    for device in devices:
        name = device["hostname"]
        print(f"Checking {name} ({device['ip']}) ...")
        status, detail, output = collect(device, password)
        if status == "OK":
            save_output(name, output)
        print(f"  {status}: {detail}")
        results.append({"hostname": name, "ip": device["ip"],
                        "status": status, "detail": detail})

    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"\nSummary: {ok} of {len(results)} devices succeeded")

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = reports_dir / f"multi_device_summary_{stamp}.csv"
    with open(report, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["hostname", "ip", "status", "detail"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Report saved to {report}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
