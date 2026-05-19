from __future__ import annotations

from datetime import datetime
from pathlib import Path


class IRLogger:
    COLORS = {
        "INFO": "\033[37m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "SUCCESS": "\033[32m",
    }
    RESET = "\033[0m"

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"IRCollection_{datetime.now():%Y%m%d}.log"

    def log(self, message: str, level: str = "INFO") -> None:
        level = level.upper()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        color = self.COLORS.get(level, self.COLORS["INFO"])
        print(f"{color}{entry}{self.RESET}")
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(entry + "\n")

