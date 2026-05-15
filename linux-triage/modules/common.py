from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def run_command(command: list[str], output_file: Path, logger, timeout: int = 60) -> bool:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output_file.write_text(
            result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else ""),
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return True
        logger.log(f"Command returned {result.returncode}: {' '.join(command)}", "WARNING")
        return False
    except FileNotFoundError:
        logger.log(f"Command not found: {command[0]}", "WARNING")
    except subprocess.TimeoutExpired:
        logger.log(f"Command timed out: {' '.join(command)}", "WARNING")
    except Exception as exc:
        logger.log(f"Command failed {' '.join(command)}: {exc}", "WARNING")
    return False


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_read_text(path: Path, max_bytes: int = 1024 * 1024) -> str:
    with path.open("rb") as handle:
        return handle.read(max_bytes).decode("utf-8", errors="replace")


def copy_path(source: Path, destination: Path, logger, max_file_bytes: int) -> int:
    if not source.exists():
        return 0
    copied = 0
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            if source.stat().st_size <= max_file_bytes:
                shutil.copy2(source, destination)
                return 1
            logger.log(f"Skipping oversized file: {source}", "WARNING")
        except Exception as exc:
            logger.log(f"Failed to copy {source}: {exc}", "WARNING")
        return 0

    for root, dirs, files in os.walk(source, topdown=True, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(source)
        dirs[:] = [name for name in dirs if not (root_path / name).is_symlink()]
        for filename in files:
            src_file = root_path / filename
            if src_file.is_symlink():
                continue
            try:
                if src_file.stat().st_size > max_file_bytes:
                    logger.log(f"Skipping oversized file: {src_file}", "WARNING")
                    continue
                dst_file = destination / rel_root / filename
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                copied += 1
            except Exception as exc:
                logger.log(f"Failed to copy {src_file}: {exc}", "WARNING")
    return copied


def existing_paths(paths: Iterable[str]) -> list[Path]:
    return [Path(item) for item in paths if Path(item).exists()]
