"""
System Artifacts Collection — Linux equivalent of Modules/FileSystemArtifacts.ps1

Collects:
  - /var/log/   (system & application logs)
  - Key /etc/   configuration files (mirrors Registry hives)
  - /proc/      system information snapshot (OS version, cmdline, modules, mounts)
"""

import os
import shutil
import subprocess

from Core.logger import log_ir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return result.stdout
    except Exception as exc:
        log_ir(f"Command {cmd} failed: {exc}", level="WARNING")
        return ""


def _mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _copy_tree(src: str, dest: str, description: str) -> None:
    """
    Recursively copy *src* into *dest*.
    Mirrors the Copy-Item -Recurse pattern from FileSystemArtifacts.ps1.
    """
    if not os.path.exists(src):
        log_ir(f"Path not found: {src}", level="WARNING")
        return
    try:
        _mkdir(dest)
        count = 0
        for root, _dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_dir = os.path.join(dest, rel)
            _mkdir(target_dir)
            for fname in files:
                src_file = os.path.join(root, fname)
                dst_file = os.path.join(target_dir, fname)
                try:
                    shutil.copy2(src_file, dst_file)
                    count += 1
                except OSError as exc:
                    log_ir(f"Could not copy {src_file}: {exc}", level="WARNING")
        log_ir(f"Collected {count} files from {description}", level="SUCCESS")
    except Exception as exc:
        log_ir(f"Failed to collect {description}: {exc}", level="ERROR")


def _copy_file(src: str, dest: str, description: str) -> None:
    if not os.path.isfile(src):
        log_ir(f"File not found: {src}", level="WARNING")
        return
    try:
        _mkdir(os.path.dirname(dest))
        shutil.copy2(src, dest)
        log_ir(f"Collected {description}", level="SUCCESS")
    except OSError as exc:
        log_ir(f"Failed to collect {description}: {exc}", level="WARNING")


# ---------------------------------------------------------------------------
# /var/log/  (mirrors Event Logs collection in Get-WindowsArtifacts)
# ---------------------------------------------------------------------------

def collect_logs(output_path: str) -> None:
    """Copy /var/log/ into System/Logs/."""
    log_ir("Collecting system logs (/var/log/)...")

    dest = os.path.join(output_path, "System", "Logs")
    _copy_tree("/var/log", dest, "/var/log/")


# ---------------------------------------------------------------------------
# /etc/  (mirrors Registry hive collection — system config as ground truth)
# ---------------------------------------------------------------------------

def collect_etc(output_path: str) -> None:
    """
    Copy forensically relevant /etc/ files.
    Mirrors Get-RegistryHives — these files expose user accounts, sudo rules,
    PAM config, SSH config, scheduled tasks, and network settings.
    """
    log_ir("Collecting /etc/ configuration files...")

    etc_dest = os.path.join(output_path, "System", "etc")
    _mkdir(etc_dest)

    # Individual high-value files
    single_files = [
        ("/etc/passwd",         "passwd",         "User accounts"),
        ("/etc/shadow",         "shadow",          "Password hashes"),
        ("/etc/group",          "group",           "Group definitions"),
        ("/etc/gshadow",        "gshadow",         "Group password hashes"),
        ("/etc/sudoers",        "sudoers",         "Sudo rules"),
        ("/etc/hosts",          "hosts",           "Hosts file"),
        ("/etc/hostname",       "hostname",        "Hostname"),
        ("/etc/os-release",     "os-release",      "OS version"),
        ("/etc/timezone",       "timezone",        "Timezone"),
        ("/etc/crontab",        "crontab",         "System crontab"),
        ("/etc/shells",         "shells",          "Valid login shells"),
        ("/etc/environment",    "environment",     "Global environment"),
        ("/etc/profile",        "profile",         "Global shell profile"),
        ("/etc/bashrc",         "bashrc",          "Global bashrc"),
        ("/etc/login.defs",     "login.defs",      "Login configuration"),
        ("/etc/fstab",          "fstab",           "Filesystem mounts"),
        ("/etc/resolv.conf",    "resolv.conf",     "DNS resolver config"),
        ("/etc/nsswitch.conf",  "nsswitch.conf",   "Name service switch"),
        ("/etc/security/limits.conf", os.path.join("security", "limits.conf"), "Resource limits"),
    ]

    for src, rel_dest, desc in single_files:
        _copy_file(src, os.path.join(etc_dest, rel_dest), desc)

    # Directories
    dir_paths = [
        ("/etc/sudoers.d",      "sudoers.d",       "Sudoers drop-in files"),
        ("/etc/ssh",            "ssh",             "SSH configuration"),
        ("/etc/pam.d",          "pam.d",           "PAM configuration"),
        ("/etc/profile.d",      "profile.d",       "Shell profile drop-ins"),
        ("/etc/cron.d",         "cron.d",          "Cron drop-in jobs"),
        ("/etc/cron.daily",     "cron.daily",      "Daily cron jobs"),
        ("/etc/cron.weekly",    "cron.weekly",     "Weekly cron jobs"),
        ("/etc/cron.monthly",   "cron.monthly",    "Monthly cron jobs"),
        ("/etc/cron.hourly",    "cron.hourly",     "Hourly cron jobs"),
        ("/etc/network",        "network",         "Network configuration"),
        ("/etc/NetworkManager", "NetworkManager",  "NetworkManager configuration"),
        ("/etc/sysctl.d",       "sysctl.d",        "Kernel parameter overrides"),
        ("/etc/ld.so.conf.d",   "ld.so.conf.d",    "Dynamic linker config"),
        ("/etc/modprobe.d",     "modprobe.d",      "Kernel module config"),
    ]

    for src, rel_dest, desc in dir_paths:
        _copy_tree(src, os.path.join(etc_dest, rel_dest), desc)


# ---------------------------------------------------------------------------
# /proc/ snapshot  (no direct PS1 equivalent — captures volatile kernel state)
# ---------------------------------------------------------------------------

def collect_proc_info(output_path: str) -> None:
    """
    Dump key /proc/ pseudo-files and command outputs that capture the kernel
    and hardware state at collection time.
    """
    log_ir("Collecting /proc/ system information...")

    proc_dest = os.path.join(output_path, "System", "proc_snapshot")
    _mkdir(proc_dest)

    # Direct /proc/ file copies
    proc_files = [
        ("/proc/version",       "version.txt",       "Kernel version"),
        ("/proc/cmdline",       "cmdline.txt",        "Kernel boot command line"),
        ("/proc/cpuinfo",       "cpuinfo.txt",        "CPU information"),
        ("/proc/meminfo",       "meminfo.txt",        "Memory information"),
        ("/proc/mounts",        "mounts.txt",         "Current mounts"),
        ("/proc/net/arp",       "net_arp.txt",        "ARP table (/proc)"),
        ("/proc/net/tcp",       "net_tcp.txt",        "TCP sockets (/proc)"),
        ("/proc/net/tcp6",      "net_tcp6.txt",       "TCP6 sockets (/proc)"),
        ("/proc/net/udp",       "net_udp.txt",        "UDP sockets (/proc)"),
        ("/proc/net/udp6",      "net_udp6.txt",       "UDP6 sockets (/proc)"),
        ("/proc/net/if_inet6",  "net_if_inet6.txt",   "IPv6 interfaces"),
        ("/proc/net/dev",       "net_dev.txt",        "Network interface stats"),
        ("/proc/sys/kernel/hostname",  "kernel_hostname.txt",  "Kernel hostname"),
        ("/proc/sys/kernel/osrelease", "kernel_osrelease.txt", "Kernel OS release"),
    ]

    for src, fname, desc in proc_files:
        _copy_file(src, os.path.join(proc_dest, fname), desc)

    # Command output dumps
    commands = [
        (["lsmod"],                                   "lsmod.txt",         "Loaded kernel modules"),
        (["lsblk", "-o", "NAME,TYPE,SIZE,FSTYPE,MOUNTPOINT,UUID"], "lsblk.txt", "Block devices"),
        (["df", "-h"],                                "df.txt",            "Disk usage"),
        (["uname", "-a"],                             "uname.txt",         "Kernel/machine info"),
        (["hostname", "-I"],                          "ip_addresses.txt",  "IP addresses"),
        (["ip", "addr", "show"],                      "ip_addr.txt",       "Network interfaces"),
        (["uptime"],                                  "uptime.txt",        "System uptime"),
        (["dmesg"],                                   "dmesg.txt",         "Kernel ring buffer"),
        (["timedatectl", "status"],                   "timedatectl.txt",   "Time/timezone info"),
        (["systemctl", "list-units", "--all", "--no-pager"], "systemd_units.txt", "All systemd units"),
        (["env"],                                     "environment.txt",   "Current environment"),
    ]

    for cmd, fname, desc in commands:
        output = _run(cmd)
        if output:
            try:
                with open(os.path.join(proc_dest, fname), "w", encoding="utf-8") as fh:
                    fh.write(output)
                log_ir(f"Collected {desc}", level="SUCCESS")
            except OSError as exc:
                log_ir(f"Failed to write {desc}: {exc}", level="WARNING")
        else:
            log_ir(f"{desc} returned no output (command may not be available)", level="WARNING")
