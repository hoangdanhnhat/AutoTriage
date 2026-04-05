import os
import sys
from datetime import datetime

# ANSI colour codes
_COLOURS = {
    "INFO":    "\033[97m",   # White
    "WARNING": "\033[93m",   # Yellow
    "ERROR":   "\033[91m",   # Red
    "SUCCESS": "\033[92m",   # Green
    "RESET":   "\033[0m",
}

# Will be set by main_collector once CONFIG is available
_log_path: str = ""


def set_log_path(path: str) -> None:
    """Called by main_collector after the log directory is created."""
    global _log_path
    _log_path = path


def log_ir(message: str, level: str = "INFO") -> None:
    """
    Write a timestamped log entry to stdout (with ANSI colour) and to
    the daily log file (plain text), mirroring Write-IRLog in Logger.ps1.
    """
    level = level.upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"

    # Console output with colour
    colour = _COLOURS.get(level, _COLOURS["INFO"])
    print(f"{colour}{entry}{_COLOURS['RESET']}", file=sys.stdout, flush=True)

    # File output
    if _log_path:
        log_file = os.path.join(
            _log_path,
            f"IRCollection_{datetime.now().strftime('%Y%m%d')}.log"
        )
        try:
            with open(log_file, "a", encoding="utf-8") as fh:
                fh.write(entry + "\n")
        except OSError:
            pass  # Never let logging crash the collection
