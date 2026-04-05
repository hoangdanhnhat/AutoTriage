"""
Volatile Data Collection — Linux equivalent of Modules/VolatileData.ps1

Collection order (most volatile first):
  1. Running processes  (/proc/{pid}/)
  2. Network connections (ss)
  3. Logged-in users    (who / last)
  4. ARP table & routing table (ip neigh / ip route)
"""

import csv
import json
import os
import subprocess
from pathlib import Path

from Core.config import CONFIG
from Core.logger import log_ir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> str:
    """Run *cmd* and return stdout as a string; return '' on error."""
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


# ---------------------------------------------------------------------------
# Memory dump  (mirrors Get-MemoryDump)
# ---------------------------------------------------------------------------

def collect_memory_dump(output_path: str) -> dict | None:
    """
    Attempt a memory acquisition using 'avml' or 'lime' if present in Tools/.
    Default CONFIG['collect_memory'] is False — most deployments skip this.
    """
    log_ir("Starting memory acquisition...")

    tools_path = CONFIG["tools_path"]
    avml = os.path.join(tools_path, "avml")
    mem_dir = os.path.join(output_path, "Memory")
    _mkdir(mem_dir)
    mem_file = os.path.join(mem_dir, "memory.lime")

    if os.path.isfile(avml):
        try:
            subprocess.run([avml, mem_file], check=True, timeout=600)
            size = os.path.getsize(mem_file)
            log_ir(f"Memory dump completed: {mem_file} ({round(size / (1024**3), 2)} GB)", level="SUCCESS")
            return {"file_path": mem_file, "size": size}
        except Exception as exc:
            log_ir(f"Memory dump failed: {exc}", level="ERROR")
    else:
        log_ir("Memory acquisition tool (avml) not found in Tools/ — skipping.", level="WARNING")

    return None


# ---------------------------------------------------------------------------
# Process list  (mirrors Get-ProcessList)
# ---------------------------------------------------------------------------

def collect_process_list(output_path: str) -> None:
    """
    Read /proc/{pid}/ entries for every running process and write:
      - processes.csv  (tabular summary)
      - processes.json (full detail including cmdline, environ, parent pid)
    """
    log_ir("Collecting running processes...")

    volatile_dir = os.path.join(output_path, "Volatile")
    _mkdir(volatile_dir)

    processes = []

    for entry in sorted(os.listdir("/proc")):
        if not entry.isdigit():
            continue
        pid = entry
        proc_base = f"/proc/{pid}"

        try:
            # --- cmdline ---
            with open(f"{proc_base}/cmdline", "rb") as fh:
                cmdline = fh.read().replace(b"\x00", b" ").decode(errors="replace").strip()

            # --- status (Name, PPid, Uid) ---
            status: dict[str, str] = {}
            with open(f"{proc_base}/status", "r", errors="replace") as fh:
                for line in fh:
                    if ":" in line:
                        k, _, v = line.partition(":")
                        status[k.strip()] = v.strip()

            # --- exe symlink (may be inaccessible) ---
            try:
                exe_path = os.readlink(f"{proc_base}/exe")
            except OSError:
                exe_path = ""

            # --- environ (first 4 KB to avoid huge dumps) ---
            try:
                with open(f"{proc_base}/environ", "rb") as fh:
                    raw_env = fh.read(4096)
                environ_pairs = raw_env.replace(b"\x00", b"\n").decode(errors="replace").splitlines()
            except OSError:
                environ_pairs = []

            processes.append({
                "pid":         pid,
                "name":        status.get("Name", ""),
                "ppid":        status.get("PPid", ""),
                "uid":         status.get("Uid", "").split()[0] if status.get("Uid") else "",
                "exe_path":    exe_path,
                "cmdline":     cmdline,
                "vm_rss_kb":   status.get("VmRSS", "").replace(" kB", "").strip(),
                "threads":     status.get("Threads", ""),
                "environ":     environ_pairs,
            })
        except OSError:
            # Process may have exited between the listdir and the read
            continue

    # CSV (without environ — too wide)
    csv_file = os.path.join(volatile_dir, "processes.csv")
    csv_fields = ["pid", "name", "ppid", "uid", "exe_path", "cmdline", "vm_rss_kb", "threads"]
    with open(csv_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(processes)

    # JSON (full detail including environ)
    json_file = os.path.join(volatile_dir, "processes.json")
    with open(json_file, "w", encoding="utf-8") as fh:
        json.dump(processes, fh, indent=2)

    log_ir(f"Collected {len(processes)} processes", level="SUCCESS")


# ---------------------------------------------------------------------------
# Network connections  (mirrors Get-NetworkConnections)
# ---------------------------------------------------------------------------

def collect_network_connections(output_path: str) -> None:
    """
    Collect active TCP/UDP sockets using 'ss' and write:
      - network_connections.csv
      - listening_ports.csv
      - arp_table.txt
      - routing_table.txt
    """
    log_ir("Collecting network connections...")

    volatile_dir = os.path.join(output_path, "Volatile")
    _mkdir(volatile_dir)

    # --- all TCP/UDP connections ---
    raw_all = _run(["ss", "-tupna"])
    conn_file = os.path.join(volatile_dir, "network_connections.txt")
    with open(conn_file, "w", encoding="utf-8") as fh:
        fh.write(raw_all)

    # --- listening ports only ---
    raw_listen = _run(["ss", "-tlnp"])
    listen_file = os.path.join(volatile_dir, "listening_ports.txt")
    with open(listen_file, "w", encoding="utf-8") as fh:
        fh.write(raw_listen)

    log_ir("Network connections collected", level="SUCCESS")


# ---------------------------------------------------------------------------
# ARP table & routing table  (no direct Windows equivalent; maps to low-level net info)
# ---------------------------------------------------------------------------

def collect_arp_routing(output_path: str) -> None:
    log_ir("Collecting ARP table and routing table...")

    volatile_dir = os.path.join(output_path, "Volatile")
    _mkdir(volatile_dir)

    arp_out = _run(["ip", "neigh", "show"])
    with open(os.path.join(volatile_dir, "arp_table.txt"), "w", encoding="utf-8") as fh:
        fh.write(arp_out)

    route_out = _run(["ip", "route", "show"])
    with open(os.path.join(volatile_dir, "routing_table.txt"), "w", encoding="utf-8") as fh:
        fh.write(route_out)

    log_ir("ARP and routing table collected", level="SUCCESS")


# ---------------------------------------------------------------------------
# Logged-in users
# ---------------------------------------------------------------------------

def collect_logged_users(output_path: str) -> None:
    log_ir("Collecting logged-in users...")

    volatile_dir = os.path.join(output_path, "Volatile")
    _mkdir(volatile_dir)

    who_out = _run(["who", "-a"])
    with open(os.path.join(volatile_dir, "logged_users.txt"), "w", encoding="utf-8") as fh:
        fh.write(who_out)

    last_out = _run(["last", "-n", "200"])
    with open(os.path.join(volatile_dir, "login_history.txt"), "w", encoding="utf-8") as fh:
        fh.write(last_out)

    lastb_out = _run(["lastb", "-n", "200"])
    with open(os.path.join(volatile_dir, "failed_logins.txt"), "w", encoding="utf-8") as fh:
        fh.write(lastb_out)

    log_ir("Logged-in users collected", level="SUCCESS")
