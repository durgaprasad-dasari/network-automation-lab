# Network Automation Lab (CML-Free + Python + Netmiko)

Beginner-level network automation practice built on a free virtual Cisco lab.
All work is done against a **lab I built myself**, never against production devices.

## Lab setup
- Cisco Modeling Labs Free (CML-Free) running as a VM in VMware Workstation Pro on a Windows 11 PC
- 3 virtual devices: one IOL router (R1) and two IOL-L2 switches (SW1, SW2)
- Devices are reached over SSH from the PC through a bridge to the VMware network
- Python 3 in a virtual environment, with the Netmiko library

## What is in this repository
| File | What it does | Status |
|---|---|---|
| `scripts/check_setup.py` | Checks Python version, lab files and optional libraries | Working |
| `scripts/first_netmiko_connect.py` | Connects to one lab router and runs `show ip interface brief` | Tested on my lab |
| `scripts/multi_device_show.py` | Runs the same command on every device in `data/inventory.csv`, saves output and a CSV report | Tested on my lab |
| `scripts/backup_configs.py` | Saves timestamped `show running-config` backups and reports changes | Tested on my lab |

`data/mock_outputs/` holds sample text written for practice (not captured from a device).
`data/inventory_with_errors.csv` has deliberately invalid IPs for validation practice.

## How to run
```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install netmiko
python scripts/multi_device_show.py
```
The script asks for the lab password (hidden). It can also read `LAB_PASSWORD` and `LAB_USERNAME`
environment variables. No password is stored in any file.

## Sample output (from my CML-Free lab)
```
Checking R1 (10.10.10.1) ...
  OK: down: Ethernet0/2, Ethernet0/3
Checking SW1 (10.10.10.11) ...
  OK: no down interfaces
Checking SW2 (10.10.10.12) ...
  OK: no down interfaces

Summary: 3 of 3 devices succeeded
```

## Safety
- Scripts only send read-only `show` commands.
- Credentials are never hardcoded. `.env`, backups, reports and live device output are excluded by `.gitignore`.
- Configuration backups can contain password hashes, so they are never committed.
- Only run against devices you are authorised to use.

## What I learned / next steps
- Building a virtual Cisco lab, configuring SSH, and troubleshooting a return-path routing problem
- Using Python and Netmiko for multi-device read-only collection with error handling
- Next: configuration drift checks, a health report, Ansible basics, AWS networking with Boto3
