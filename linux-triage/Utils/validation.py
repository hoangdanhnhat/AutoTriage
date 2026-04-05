import os
import shutil

from Core.logger import log_ir


def check_root() -> bool:
    """Return True if the process is running as root (uid 0)."""
    if os.geteuid() != 0:
        log_ir("This script requires root privileges!", level="ERROR")
        return False
    return True


def check_disk_space(path: str, required_gb: float = 10.0) -> bool:
    """
    Return True if *path* has at least *required_gb* of free space.
    Mirrors Test-DiskSpace in Utils/Validation.ps1.
    """
    usage = shutil.disk_usage(path)
    free_gb = round(usage.free / (1024 ** 3), 2)

    if free_gb < required_gb:
        log_ir(
            f"Insufficient disk space: {free_gb} GB available, "
            f"{required_gb} GB required",
            level="ERROR",
        )
        return False
    return True
