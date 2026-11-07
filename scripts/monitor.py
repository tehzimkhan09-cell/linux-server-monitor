#!/usr/bin/env python3

import time
import shutil
import socket
import platform
import subprocess

from pathlib import Path
from datetime import datetime


# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"

LOG_FILE = LOG_DIR / "monitor.log"
REPORT_FILE = REPORT_DIR / "health_report.txt"


# Alert Thresholds
CPU_WARNING = 70
CPU_CRITICAL = 90

RAM_WARNING = 70
RAM_CRITICAL = 90

DISK_WARNING = 80
DISK_CRITICAL = 90


# CPU Monitoring
def get_cpu_usage():

    def read_cpu():
        with open("/proc/stat", "r") as file:
            values = list(map(int, file.readline().split()[1:]))

        idle = values[3] + values[4]
        total = sum(values)

        return idle, total

    idle1, total1 = read_cpu()

    time.sleep(1)

    idle2, total2 = read_cpu()

    total_diff = total2 - total1
    idle_diff = idle2 - idle1

    if total_diff <= 0:
        return 0.0

    usage = (1 - idle_diff / total_diff) * 100

    return round(usage, 2)


# RAM Monitoring
def get_ram_usage():

    memory = {}

    with open("/proc/meminfo", "r") as file:

        for line in file:
            key, value = line.split(":", 1)
            memory[key] = int(value.strip().split()[0])

    total = memory["MemTotal"]
    available = memory["MemAvailable"]

    used = total - available

    percentage = (used / total) * 100

    return (
        round(percentage, 2),
        total // 1024,
        used // 1024
    )


# Disk Monitoring
def get_disk_usage():

    disk = shutil.disk_usage("/")

    percentage = (disk.used / disk.total) * 100

    return (
        round(percentage, 2),
        disk.total,
        disk.used,
        disk.free
    )


# System Uptime
def get_uptime():

    with open("/proc/uptime", "r") as file:
        seconds = float(file.readline().split()[0])

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    return f"{hours} hours {minutes} minutes"


# Process Monitoring
def get_top_processes():

    result = subprocess.run(
        [
            "ps",
            "-eo",
            "pid,comm,%cpu,%mem",
            "--sort=-%cpu"
        ],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        return "Process information unavailable."

    return "\n".join(result.stdout.splitlines()[:6])


# Alert Checking
def check_status(value, warning, critical):

    if value >= critical:
        return "CRITICAL"

    elif value >= warning:
        return "WARNING"

    else:
        return "NORMAL"


# Main Monitoring Function
def main():

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )

    hostname = socket.gethostname()
    operating_system = platform.system()
    uptime = get_uptime()

    # Collect Metrics
    cpu = get_cpu_usage()

    ram, total_ram, used_ram = get_ram_usage()

    disk, total_disk, used_disk, free_disk = get_disk_usage()

    # Generate Report
    report = [

        "=" * 55,

        "       LINUX SERVER HEALTH REPORT",

        "=" * 55,

        f"Date       : {timestamp}",

        f"Hostname   : {hostname}",

        f"OS         : {operating_system}",

        f"Uptime     : {uptime}",

        "",

        "RESOURCE UTILIZATION",

        "-" * 55,

        f"CPU Usage  : {cpu}%",

        f"RAM Usage  : {ram}%",

        f"RAM Used   : {used_ram} MB / {total_ram} MB",

        f"Disk Usage : {disk}%",

        "",

        "HEALTH STATUS",

        "-" * 55,

        f"{check_status(cpu, CPU_WARNING, CPU_CRITICAL):8} | CPU  | {cpu}%",

        f"{check_status(ram, RAM_WARNING, RAM_CRITICAL):8} | RAM  | {ram}%",

        f"{check_status(disk, DISK_WARNING, DISK_CRITICAL):8} | DISK | {disk}%",

        "",

        "DISK INFORMATION",

        "-" * 55,

        f"Total : {total_disk // (1024 ** 3)} GB",

        f"Used  : {used_disk // (1024 ** 3)} GB",

        f"Free  : {free_disk // (1024 ** 3)} GB",

        "",

        "TOP 5 CPU PROCESSES",

        "-" * 55,

        get_top_processes(),

        "=" * 55

    ]

    output = "\n".join(report) + "\n"

    # Display Report
    print(output)

    # Save Monitoring Logs
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(output + "\n")

    # Save Latest Report
    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        file.write(output)

    print("Monitoring completed successfully!")

    print(f"Log saved: {LOG_FILE}")

    print(f"Report saved: {REPORT_FILE}")


# Program Entry Point
if __name__ == "__main__":
    main()
