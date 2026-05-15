from __future__ import annotations

import pwd
from pathlib import Path

from modules.common import copy_path, existing_paths, run_command


def collect_system_artifacts(output_path: Path, logger, max_file_bytes: int) -> None:
    logger.log("Collecting Linux system artifacts...", "INFO")
    base = output_path / "System"
    targets = [
        ("/etc/passwd", "etc/passwd"),
        ("/etc/group", "etc/group"),
        ("/etc/shadow", "etc/shadow"),
        ("/etc/sudoers", "etc/sudoers"),
        ("/etc/sudoers.d", "etc/sudoers.d"),
        ("/etc/ssh", "etc/ssh"),
        ("/etc/hosts", "etc/hosts"),
        ("/etc/resolv.conf", "etc/resolv.conf"),
        ("/etc/fstab", "etc/fstab"),
        ("/etc/crontab", "etc/crontab"),
        ("/etc/cron.d", "etc/cron.d"),
        ("/etc/cron.daily", "etc/cron.daily"),
        ("/etc/cron.hourly", "etc/cron.hourly"),
        ("/etc/cron.weekly", "etc/cron.weekly"),
        ("/etc/systemd/system", "etc/systemd/system"),
        ("/usr/lib/systemd/system", "usr/lib/systemd/system"),
        ("/var/spool/cron", "var/spool/cron"),
        ("/var/spool/cron/crontabs", "var/spool/cron/crontabs"),
        ("/var/lib/systemd", "var/lib/systemd"),
        ("/var/lib/dpkg/status", "packages/dpkg_status"),
        ("/var/lib/rpm", "packages/rpm"),
    ]
    for source, relative_dest in targets:
        copied = copy_path(Path(source), base / relative_dest, logger, max_file_bytes)
        if copied:
            logger.log(f"Collected {copied} files from {source}", "SUCCESS")

    run_command(["uname", "-a"], base / "system_info" / "uname.txt", logger)
    run_command(["hostnamectl"], base / "system_info" / "hostnamectl.txt", logger)
    run_command(["journalctl", "--list-boots", "--no-pager"], base / "logs" / "journal_boots.txt", logger)
    run_command(["journalctl", "--no-pager", "-n", "5000"], base / "logs" / "journal_recent.txt", logger, timeout=120)


def collect_log_artifacts(output_path: Path, logger, max_file_bytes: int) -> None:
    logger.log("Collecting log artifacts...", "INFO")
    log_dest = output_path / "Logs"
    for log_path in existing_paths(["/var/log/auth.log", "/var/log/secure", "/var/log/syslog", "/var/log/messages", "/var/log/audit", "/var/log/nginx", "/var/log/apache2"]):
        copied = copy_path(log_path, log_dest / log_path.relative_to("/"), logger, max_file_bytes)
        if copied:
            logger.log(f"Collected {copied} files from {log_path}", "SUCCESS")


def collect_user_artifacts(output_path: Path, logger, max_file_bytes: int) -> None:
    logger.log("Collecting user profile artifacts...", "INFO")
    users_base = output_path / "Users"
    interesting_files = [
        ".bash_history",
        ".zsh_history",
        ".python_history",
        ".mysql_history",
        ".psql_history",
        ".viminfo",
        ".profile",
        ".bashrc",
        ".zshrc",
        ".ssh",
        ".config/autostart",
        ".local/share/recently-used.xbel",
        ".mozilla/firefox",
        ".config/google-chrome/Default/History",
        ".config/google-chrome/Default/Login Data",
        ".config/chromium/Default/History",
        ".config/chromium/Default/Login Data",
    ]
    for user in pwd.getpwall():
        home = Path(user.pw_dir)
        if not home.is_absolute() or not home.exists() or str(home) in ["/", "/nonexistent"]:
            continue
        user_dest = users_base / user.pw_name
        logger.log(f"Collecting artifacts for user: {user.pw_name}", "INFO")
        for relative in interesting_files:
            source = home / relative
            if source.exists():
                copied = copy_path(source, user_dest / relative, logger, max_file_bytes)
                if copied:
                    logger.log(f"Collected {copied} files from {source}", "SUCCESS")


def collect_filesystem_artifacts(output_path: Path, logger) -> None:
    logger.log("Collecting filesystem metadata...", "INFO")
    base = output_path / "Filesystem"
    run_command(["findmnt", "-a"], base / "findmnt.txt", logger)
    run_command(["lsblk", "-f"], base / "lsblk_f.txt", logger)
    run_command(["find", "/tmp", "-xdev", "-maxdepth", "2", "-printf", "%p|%u|%g|%m|%s|%TY-%Tm-%Td %TH:%TM:%TS\\n"], base / "tmp_listing.txt", logger, timeout=120)
    run_command(["find", "/var/tmp", "-xdev", "-maxdepth", "2", "-printf", "%p|%u|%g|%m|%s|%TY-%Tm-%Td %TH:%TM:%TS\\n"], base / "var_tmp_listing.txt", logger, timeout=120)

