import os

# Base directory is two levels up from this file (linux-triage/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {
    "collection_name":          "IR-Triage-Collection",
    "output_path":              os.path.join(_BASE_DIR, "Output"),
    "log_path":                 os.path.join(_BASE_DIR, "Logs"),
    "tools_path":               os.path.join(_BASE_DIR, "Tools"),

    # Collection toggles — enable/disable specific artifact collection
    "collect_memory":           False,   # Requires lime-forensics or avml
    "collect_volatile":         True,    # Process list, network connections, logged users
    "collect_system":           True,    # /var/log/, /etc/, /proc/ info, kernel modules
    "collect_persistence":      True,    # Cron, systemd, init.d, SUID files, 3rd-party apps
    "collect_user":             True,    # Shell history, SSH keys, browser data, dotfiles
    "compress":                 True,    # Compress output to .tar.gz (required for Ansible transfer)

    # Hash algorithm
    "hash_algorithm":           "sha256",
}
