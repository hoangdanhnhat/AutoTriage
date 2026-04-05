"""
User Artifacts Collection — Linux equivalent of Get-UserArtifacts in
Modules/FileSystemArtifacts.ps1

For each user profile under /home/ (plus /root/), collects:
  - Shell history files   (~/.bash_history, ~/.zsh_history, ~/.sh_history, etc.)
  - SSH keys & known_hosts (~/.ssh/)
  - Shell rc/profile files (~/.bashrc, ~/.profile, ~/.zshrc, ~/.bash_profile, etc.)
  - XDG autostart entries (~/.config/autostart/)
  - Browser profiles      (Chrome, Chromium, Firefox)
  - .netrc                (stored credentials)
  - Systemd user units    (~/.config/systemd/user/)
  - Recently used files   (~/.local/share/recently-used.xbel)
"""

import os
import shutil

from Core.logger import log_ir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _copy_tree(src: str, dest: str, description: str) -> None:
    if not os.path.exists(src):
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
        if count > 0:
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
# Per-user collection
# ---------------------------------------------------------------------------

def collect_user_artifacts(output_path: str) -> None:
    """
    Iterate every user profile directory and collect forensic artifacts.
    Mirrors Get-UserArtifacts which iterates C:\\Users\\.
    """
    log_ir("Collecting user profile artifacts...")

    users_base = os.path.join(output_path, "Users")
    _mkdir(users_base)

    # Build list of (username, home_dir) pairs — /etc/passwd is the authoritative source
    profiles: list[tuple[str, str]] = []
    try:
        with open("/etc/passwd", "r") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split(":")
                if len(parts) < 7:
                    continue
                username   = parts[0]
                home_dir   = parts[5]
                # Skip system accounts (uid < 1000) except root
                try:
                    uid = int(parts[2])
                except ValueError:
                    continue
                if uid != 0 and uid < 1000:
                    continue
                if os.path.isdir(home_dir):
                    profiles.append((username, home_dir))
    except OSError as exc:
        log_ir(f"Could not read /etc/passwd: {exc}", level="ERROR")
        return

    # Deduplicate (multiple entries can point to same home)
    seen_homes: set[str] = set()
    for username, home_dir in profiles:
        if home_dir in seen_homes:
            continue
        seen_homes.add(home_dir)

        log_ir(f"Collecting artifacts for user: {username}", level="INFO")
        user_dest = os.path.join(users_base, username)
        _mkdir(user_dest)

        _collect_single_user(username, home_dir, user_dest)


def _collect_single_user(username: str, home_dir: str, user_dest: str) -> None:
    """Collect all artifact categories for one user profile."""

    # --- Shell history files ---
    history_files = [
        ".bash_history", ".zsh_history", ".sh_history",
        ".python_history", ".mysql_history", ".psql_history",
        ".irb_history", ".lesshst", ".viminfo",
    ]
    hist_dest = os.path.join(user_dest, "ShellHistory")
    for fname in history_files:
        src = os.path.join(home_dir, fname)
        _copy_file(src, os.path.join(hist_dest, fname), f"{fname} for {username}")

    # --- SSH directory ---
    _copy_tree(
        os.path.join(home_dir, ".ssh"),
        os.path.join(user_dest, "SSH"),
        f".ssh/ for {username}",
    )

    # --- Shell rc / profile files ---
    rc_files = [
        ".bashrc", ".bash_profile", ".bash_logout", ".profile",
        ".zshrc", ".zprofile", ".zlogout", ".zshenv",
        ".xprofile", ".xinitrc", ".xsession",
    ]
    rc_dest = os.path.join(user_dest, "ShellConfig")
    for fname in rc_files:
        src = os.path.join(home_dir, fname)
        _copy_file(src, os.path.join(rc_dest, fname), f"{fname} for {username}")

    # --- XDG autostart entries (user-level persistence) ---
    _copy_tree(
        os.path.join(home_dir, ".config", "autostart"),
        os.path.join(user_dest, "XDG_Autostart"),
        f"XDG autostart for {username}",
    )

    # --- Systemd user units ---
    _copy_tree(
        os.path.join(home_dir, ".config", "systemd", "user"),
        os.path.join(user_dest, "SystemdUser"),
        f"systemd user units for {username}",
    )

    # --- Recently used files (GNOME/XDG) ---
    _copy_file(
        os.path.join(home_dir, ".local", "share", "recently-used.xbel"),
        os.path.join(user_dest, "RecentFiles", "recently-used.xbel"),
        f"recently-used.xbel for {username}",
    )

    # --- .netrc (may contain plaintext credentials) ---
    _copy_file(
        os.path.join(home_dir, ".netrc"),
        os.path.join(user_dest, ".netrc"),
        f".netrc for {username}",
    )

    # --- Browser profiles ---
    # Mirrors Chrome/Edge/Firefox collection in Get-UserArtifacts
    browser_paths = [
        (os.path.join(home_dir, ".config", "google-chrome", "Default"),     "Chrome_Default"),
        (os.path.join(home_dir, ".config", "google-chrome"),                "Chrome"),
        (os.path.join(home_dir, ".config", "chromium", "Default"),          "Chromium_Default"),
        (os.path.join(home_dir, ".config", "chromium"),                     "Chromium"),
        (os.path.join(home_dir, ".mozilla", "firefox"),                     "Firefox"),
        (os.path.join(home_dir, ".config", "BraveSoftware", "Brave-Browser", "Default"), "Brave_Default"),
    ]
    browser_dest = os.path.join(user_dest, "BrowserData")
    for src, rel in browser_paths:
        if os.path.exists(src):
            _copy_tree(src, os.path.join(browser_dest, rel), f"{rel} for {username}")
