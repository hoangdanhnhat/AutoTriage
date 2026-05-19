from __future__ import annotations

import os
from pathlib import Path

from modules.common import run_command, safe_read_text, write_csv, write_json


def collect_memory_dump(output_path: Path, tools_path: Path, logger) -> dict | None:
    logger.log("Starting memory acquisition...")
    candidates = [tools_path / "avml", tools_path / "lime"]
    dumper = next((item for item in candidates if item.exists() and os.access(item, os.X_OK)), None)
    if dumper is None:
        logger.log("Linux memory dumper not found, skipping. Add executable avml or lime to tools/.", "WARNING")
        return None

    memory_file = output_path / "memory.raw"
    if dumper.name == "avml":
        ok = run_command([str(dumper), str(memory_file)], output_path / "memory_acquisition.log", logger, timeout=7200)
    else:
        ok = run_command([str(dumper), f"path={memory_file}", "format=raw"], output_path / "memory_acquisition.log", logger, timeout=7200)
    if ok and memory_file.exists():
        return {"file_path": str(memory_file), "size": memory_file.stat().st_size}
    return None


def collect_process_list(output_path: Path, logger) -> list[dict]:
    logger.log("Collecting running processes...")
    processes: list[dict] = []
    proc_dir = Path("/proc")
    for pid_dir in proc_dir.iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            status = _parse_status(pid_dir / "status")
            cmdline = (pid_dir / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace").strip()
            exe = os.readlink(pid_dir / "exe") if (pid_dir / "exe").exists() else ""
            processes.append(
                {
                    "pid": int(pid_dir.name),
                    "ppid": status.get("PPid", ""),
                    "name": status.get("Name", ""),
                    "uid": status.get("Uid", "").split("\t")[0],
                    "state": status.get("State", ""),
                    "exe": exe,
                    "command_line": cmdline,
                }
            )
        except Exception:
            continue

    write_csv(output_path / "processes.csv", processes)
    write_json(output_path / "processes.json", processes)
    run_command(["ps", "auxww"], output_path / "volatile" / "ps_auxww.txt", logger)
    run_command(["pstree", "-ap"], output_path / "volatile" / "pstree.txt", logger)
    logger.log(f"Collected {len(processes)} processes", "SUCCESS")
    return processes


def collect_network_connections(output_path: Path, logger) -> None:
    logger.log("Collecting network connections...")
    volatile_dir = output_path / "volatile"
    run_command(["ss", "-tunap"], volatile_dir / "network_connections.txt", logger)
    run_command(["ss", "-tulpen"], volatile_dir / "listening_ports.txt", logger)
    run_command(["ip", "addr"], volatile_dir / "ip_addr.txt", logger)
    run_command(["ip", "route"], volatile_dir / "ip_route.txt", logger)
    run_command(["arp", "-an"], volatile_dir / "arp_cache.txt", logger)
    run_command(["lsof", "-nP", "-i"], volatile_dir / "lsof_network.txt", logger)

    proc_net_dir = output_path / "proc" / "net"
    proc_net_dir.mkdir(parents=True, exist_ok=True)
    for name in ["tcp", "tcp6", "udp", "udp6", "unix", "netlink", "route", "arp"]:
        source = Path("/proc/net") / name
        if source.exists():
            (proc_net_dir / name).write_text(safe_read_text(source), encoding="utf-8")
    logger.log("Network data collected", "SUCCESS")


def collect_system_state(output_path: Path, logger) -> None:
    logger.log("Collecting volatile system state...")
    volatile_dir = output_path / "volatile"
    commands = {
        "who.txt": ["who", "-a"],
        "w.txt": ["w"],
        "last.txt": ["last", "-a"],
        "lastlog.txt": ["lastlog"],
        "uptime.txt": ["uptime"],
        "mount.txt": ["mount"],
        "df.txt": ["df", "-hT"],
        "lsblk.txt": ["lsblk", "-a", "-o", "NAME,MAJ:MIN,RM,SIZE,RO,TYPE,MOUNTPOINTS,FSTYPE,UUID"],
        "systemctl_units.txt": ["systemctl", "list-units", "--all", "--no-pager"],
        "timedatectl.txt": ["timedatectl"],
    }
    for filename, command in commands.items():
        run_command(command, volatile_dir / filename, logger)


def _parse_status(path: Path) -> dict[str, str]:
    data = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key] = value.strip()
    return data

