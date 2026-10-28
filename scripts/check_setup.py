"""Day 1 setup checker: confirms Python, optional libraries, and the lab kit files.

Read-only. Touches no network device and makes no network connection.
"""
import csv
import importlib.util
import ipaddress
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "data/inventory.csv",
    "data/inventory_with_errors.csv",
    "data/mock_outputs/R1/show_ip_interface_brief.txt",
    "data/mock_outputs/R1/show_ip_route.txt",
    "data/mock_outputs/R1/show_running-config.txt",
    "data/mock_outputs/SW1/show_vlan_brief.txt",
    "data/mock_outputs/SW2/show_vlan_brief.txt",
]
OPTIONAL_MODULES = ["requests", "yaml", "netmiko", "boto3"]


def check_python():
    ok = sys.version_info >= (3, 9)
    print(f"[{'PASS' if ok else 'FAIL'}] Python {sys.version.split()[0]} (need 3.9 or newer)")
    return ok


def check_files():
    all_ok = True
    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).is_file()
        all_ok &= exists
        print(f"[{'PASS' if exists else 'FAIL'}] {rel}")
    return all_ok


def check_inventory(rel_path):
    good, bad = 0, 0
    with open(ROOT / rel_path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                ipaddress.IPv4Address(row["ip"])
                good += 1
            except ipaddress.AddressValueError:
                bad += 1
    print(f"[INFO] {rel_path}: {good} valid IPs, {bad} invalid IPs")


def check_optional():
    for name in OPTIONAL_MODULES:
        found = importlib.util.find_spec(name) is not None
        status = "installed" if found else "not installed yet (fine until the day it is needed)"
        print(f"[INFO] {name}: {status}")


if __name__ == "__main__":
    print("=== Network Automation Lab: setup check ===")
    results = [check_python(), check_files()]
    check_inventory("data/inventory.csv")
    check_inventory("data/inventory_with_errors.csv")
    check_optional()
    print("RESULT:", "READY" if all(results) else "FIX THE FAIL LINES ABOVE")
    sys.exit(0 if all(results) else 1)
