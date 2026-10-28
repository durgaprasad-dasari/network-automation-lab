"""Back up the running configuration of every device in data/inventory.csv.

READ-ONLY: the only command sent to a device is 'show running-config'.

For each device it:
  1. validates the IP address,
  2. connects over SSH with Netmiko and reads the running config,
  3. saves it as backups/<hostname>/<hostname>_<timestamp>.cfg,
  4. compares it with the previous backup and reports NEW, UNCHANGED or CHANGED
     (a CHANGED result also saves backups/<hostname>/<hostname>_<timestamp>.diff),
and finally prints a summary and saves a CSV report in reports/.

Backups can contain password hashes. Keep the backups folder private and never
commit it to GitHub (it is listed in .gitignore). Only run this on LAB devices.
The password is never stored here: set LAB_PASSWORD or type it when asked.
"""
import csv
import difflib
import getpass
import ipaddress
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "data" / "inventory.csv"
BACKUP_DIR = ROOT / "backups"
USERNAME = os.environ.get("LAB_USERNAME", "netauto")
COMMAND = "show running-config"

# Lines that change on every run but are not real configuration changes.
VOLATILE_PREFIXES = (
    "Building configuration",
    "Current configuration",
    "! Last configuration change",
    "! NVRAM config last updated",
    "!Time:",
    "Using ",
)


def get_password():
    """Use LAB_PASSWORD if set, otherwise ask without echoing what you type."""
    password = os.environ.get("LAB_PASSWORD")
    if not password:
        password = getpass.getpass(f"Lab password for user '{USERNAME}': ")
    return password


def load_inventory(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def safe_name(hostname):
    """Make a hostname safe to use as a folder name."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", hostname)


def normalise(text):
    """Return config lines with volatile and blank lines removed, for comparing."""
    lines = []
    for line in text.splitlines():
        line = line.rstrip()
        if line and not line.startswith(VOLATILE_PREFIXES):
            lines.append(line)
    return lines


def latest_backup(device_dir):
    """Return the newest .cfg file in a device folder, or None."""
    files = sorted(device_dir.glob("*.cfg"))
    return files[-1] if files else None


def diff_changes(old_lines, new_lines):
    """Return the added/removed lines (with + and - signs) between two configs."""
    diff = difflib.unified_diff(old_lines, new_lines, "previous", "current", lineterm="")
    return [d for d in diff if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))]


def collect_config(device, password):
    """Connect to one device and read its config. Return (status, detail, config)."""
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
            config = conn.send_command(COMMAND, read_timeout=60)
    except NetmikoAuthenticationException:
        return "FAILED", "authentication failed", ""
    except NetmikoTimeoutException:
        return "FAILED", "timed out (unreachable or SSH not enabled)", ""
    except Exception as exc:  # keep going with the next device
        return "FAILED", f"{type(exc).__name__}: {exc}", ""
    if not config.strip():
        return "FAILED", "device returned an empty configuration", ""
    return "OK", "", config


def save_backup(hostname, config, stamp):
    """Save the config, compare with the previous backup, return (change, detail)."""
    device_dir = BACKUP_DIR / safe_name(hostname)
    device_dir.mkdir(parents=True, exist_ok=True)
    previous = latest_backup(device_dir)  # look BEFORE writing the new file

    new_file = device_dir / f"{safe_name(hostname)}_{stamp}.cfg"
    new_file.write_text(config + "\n")

    if previous is None:
        return "NEW", "first backup saved"

    changes = diff_changes(normalise(previous.read_text()), normalise(config))
    if not changes:
        return "UNCHANGED", "same as previous backup"

    diff_file = device_dir / f"{safe_name(hostname)}_{stamp}.diff"
    diff_file.write_text("\n".join(changes) + "\n")
    print("    Changed lines (+ added, - removed):")
    for line in changes[:20]:
        print(f"      {line}")
    if len(changes) > 20:
        print(f"      ... and {len(changes) - 20} more (see {diff_file.name})")
    return "CHANGED", f"{len(changes)} changed lines, see {diff_file.name}"


def main():
    devices = load_inventory(INVENTORY)
    password = get_password()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    for device in devices:
        name = device["hostname"]
        print(f"Backing up {name} ({device['ip']}) ...")
        status, detail, config = collect_config(device, password)
        change = ""
        if status == "OK":
            change, detail = save_backup(name, config, stamp)
        print(f"  {status}{' / ' + change if change else ''}: {detail}")
        results.append({"hostname": name, "ip": device["ip"], "status": status,
                        "change": change, "detail": detail})

    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"\nSummary: {ok} of {len(results)} backups succeeded")

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    report = reports_dir / f"backup_summary_{stamp}.csv"
    with open(report, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["hostname", "ip", "status", "change", "detail"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Report saved to {report}")
    print("Reminder: backups can contain password hashes. Keep them private.")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
