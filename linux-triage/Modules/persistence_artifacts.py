"""
Persistence Artifacts Collection — Linux equivalent of Modules/FileSystemArtifacts.ps1
(ProgramData artifacts: startup items, scheduled tasks, Defender history, 3rd-party apps)

Collects:
  - Cron jobs          (system-wide + per-user spools)
  - Systemd units      (service/timer/path units in all unit dirs)
  - SysV init scripts  (/etc/init.d/)
  - rc.local           (/etc/rc.local)
  - at jobs            (/var/spool/at/)
  - SUID/SGID files    (find / -perm /4000 or /2000)
  - 3rd-party apps     (AnyDesk, TeamViewer, etc. — mirrors ProgramData scan)
"""

import os
import shutil
import subprocess

from Core.logger import log_ir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return result.stdout
    except Exception as exc:
        log_ir(f"Command {cmd} failed: {exc}", level="WARNING")
        return ""


def _mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _copy_tree(src: str, dest: str, description: str) -> None:
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
        return
    try:
        _mkdir(os.path.dirname(dest))
        shutil.copy2(src, dest)
        log_ir(f"Collected {description}", level="SUCCESS")
    except OSError as exc:
        log_ir(f"Failed to collect {description}: {exc}", level="WARNING")


# ---------------------------------------------------------------------------
# Cron jobs  (mirrors Startup items collection)
# ---------------------------------------------------------------------------

def collect_cron(output_path: str) -> None:
    """
    Collect all cron job definitions:
      - /etc/crontab
      - /etc/cron.d/, /etc/cron.hourly/, /etc/cron.daily/, /etc/cron.weekly/, /etc/cron.monthly/
      - /var/spool/cron/crontabs/  (per-user crontabs written by 'crontab -e')
    """
    log_ir("Collecting cron jobs...")

    cron_dest = os.path.join(output_path, "Persistence", "Cron")
    _mkdir(cron_dest)

    # System-level cron files already copied by collect_etc(); copy spool here
    spool_dirs = [
        ("/var/spool/cron/crontabs", "user_crontabs", "per-user crontabs"),
        ("/var/spool/cron",          "spool_cron",    "cron spool (generic)"),
        ("/var/spool/at",            "at_jobs",       "at job queue"),
    ]
    for src, rel, desc in spool_dirs:
        _copy_tree(src, os.path.join(cron_dest, rel), desc)

    # Dump current crontabs using 'crontab -l' for each user with a shell
    try:
        with open("/etc/passwd", "r") as fh:
            users = [
                line.split(":")[0]
                for line in fh
                if not line.startswith("#") and line.strip()
            ]
    except OSError:
        users = []

    user_ctab_dir = os.path.join(cron_dest, "crontab_l_output")
    _mkdir(user_ctab_dir)
    for user in users:
        out = _run(["crontab", "-l", "-u", user])
        if out and "no crontab for" not in out:
            dest_file = os.path.join(user_ctab_dir, f"{user}.txt")
            try:
                with open(dest_file, "w", encoding="utf-8") as fh:
                    fh.write(out)
            except OSError:
                pass

    log_ir("Cron jobs collected", level="SUCCESS")


# ---------------------------------------------------------------------------
# Systemd units  (mirrors Scheduled Tasks + Startup items)
# ---------------------------------------------------------------------------

def collect_systemd(output_path: str) -> None:
    """
    Copy all systemd unit files from standard unit directories and dump
    'systemctl list-units' output.
    """
    log_ir("Collecting systemd units...")

    systemd_dest = os.path.join(output_path, "Persistence", "Systemd")
    _mkdir(systemd_dest)

    unit_dirs = [
        "/etc/systemd/system",
        "/usr/lib/systemd/system",
        "/lib/systemd/system",
        "/run/systemd/system",
        "/etc/systemd/user",
        "/usr/lib/systemd/user",
    ]
    for unit_dir in unit_dirs:
        if os.path.isdir(unit_dir):
            rel = unit_dir.strip("/").replace("/", "_")
            _copy_tree(unit_dir, os.path.join(systemd_dest, rel), f"systemd units ({unit_dir})")

    # Dump runtime unit state
    commands = [
        (["systemctl", "list-units", "--all", "--no-pager"],         "units_all.txt"),
        (["systemctl", "list-unit-files", "--all", "--no-pager"],    "unit_files.txt"),
        (["systemctl", "list-timers", "--all", "--no-pager"],        "timers.txt"),
        (["systemctl", "list-sockets", "--all", "--no-pager"],       "sockets.txt"),
    ]
    for cmd, fname in commands:
        out = _run(cmd)
        if out:
            try:
                with open(os.path.join(systemd_dest, fname), "w", encoding="utf-8") as fh:
                    fh.write(out)
            except OSError as exc:
                log_ir(f"Failed to write {fname}: {exc}", level="WARNING")

    log_ir("Systemd units collected", level="SUCCESS")


# ---------------------------------------------------------------------------
# SysV init scripts  (legacy persistence — mirrors Startup items)
# ---------------------------------------------------------------------------

def collect_init(output_path: str) -> None:
    log_ir("Collecting SysV init scripts...")

    init_dest = os.path.join(output_path, "Persistence", "InitScripts")
    _copy_tree("/etc/init.d", init_dest, "/etc/init.d/")
    _copy_file(
        "/etc/rc.local",
        os.path.join(init_dest, "rc.local"),
        "/etc/rc.local"
    )

    # rc?.d symlink targets (show run levels)
    for rc_dir in sorted(os.listdir("/etc")):
        if rc_dir.startswith("rc") and rc_dir.endswith(".d"):
            src = os.path.join("/etc", rc_dir)
            if os.path.isdir(src):
                _copy_tree(src, os.path.join(init_dest, rc_dir), f"/etc/{rc_dir}/")


# ---------------------------------------------------------------------------
# SUID / SGID files  (no direct Windows equivalent — key Linux persistence vector)
# ---------------------------------------------------------------------------

def collect_suid_files(output_path: str) -> None:
    """
    Run 'find / -perm /4000 -o -perm /2000' to enumerate SUID/SGID binaries
    and write the list to a text file.
    """
    log_ir("Enumerating SUID/SGID files (this may take a while)...")

    suid_dest = os.path.join(output_path, "Persistence")
    _mkdir(suid_dest)

    try:
        result = subprocess.run(
            ["find", "/", "-xdev",
             "(", "-perm", "-4000", "-o", "-perm", "-2000", ")",
             "-type", "f", "-ls"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        output = result.stdout
    except subprocess.TimeoutExpired:
        log_ir("SUID/SGID scan timed out after 120 s", level="WARNING")
        output = ""
    except Exception as exc:
        log_ir(f"SUID/SGID scan failed: {exc}", level="WARNING")
        output = ""

    if output:
        suid_file = os.path.join(suid_dest, "suid_sgid_files.txt")
        with open(suid_file, "w", encoding="utf-8") as fh:
            fh.write(output)
        count = output.strip().count("\n") + 1
        log_ir(f"Found {count} SUID/SGID files", level="SUCCESS")
    else:
        log_ir("No SUID/SGID file output collected", level="WARNING")


# ---------------------------------------------------------------------------
# 3rd-party application artifacts  (mirrors ProgramData 3rd-party app scan)
# ---------------------------------------------------------------------------

def collect_third_party(output_path: str) -> None:
    """
    Look for known remote-access, VPN, and collaboration tool data directories
    and copy them — mirrors the AnyDesk/TeamViewer/VPN scan in
    Get-ProgramDataArtifacts.
    """
    log_ir("Scanning for 3rd-party application artifacts...")

    tp_dest = os.path.join(output_path, "Persistence", "ThirdParty")

    # (app_name, list_of_candidate_paths)
    interesting_apps: list[tuple[str, list[str]]] = [
        ("AnyDesk",    ["/etc/anydesk", "/var/lib/anydesk", "/opt/anydesk"]),
        ("TeamViewer", ["/opt/teamviewer", "/var/log/teamviewer", "/etc/teamviewer"]),
        ("LogMeIn",    ["/opt/logmein", "/etc/logmein"]),
        ("OpenVPN",    ["/etc/openvpn", "/var/log/openvpn"]),
        ("WireGuard",  ["/etc/wireguard"]),
        ("Tailscale",  ["/var/lib/tailscale", "/etc/tailscale"]),
        ("Slack",      ["/var/lib/slack", "/opt/slack"]),
        ("Zoom",       ["/opt/zoom", "/usr/share/zoom"]),
        ("Discord",    ["/opt/discord", "/usr/share/discord"]),
        ("NordVPN",    ["/var/lib/nordvpn", "/etc/nordvpn"]),
    ]

    for app_name, candidates in interesting_apps:
        for candidate in candidates:
            if os.path.isdir(candidate):
                dest = os.path.join(tp_dest, app_name)
                _copy_tree(candidate, dest, f"{app_name} ({candidate})")
                break  # First found path is enough
