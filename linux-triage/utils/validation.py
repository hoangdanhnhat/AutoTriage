from __future__ import annotations

import os
import shutil
from pathlib import Path


def is_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def check_disk_space(path: Path, required_gb: int, logger) -> bool:
    path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(path)
    free_gb = round(usage.free / (1024**3), 2)
    if free_gb < required_gb:
        logger.log(
            f"Insufficient disk space: {free_gb}GB available, {required_gb}GB required",
            "ERROR",
        )
        return False
    logger.log(f"Disk space check passed: {free_gb}GB available", "INFO")
    return True

