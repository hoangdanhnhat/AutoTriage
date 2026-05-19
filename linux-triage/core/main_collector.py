#!/usr/bin/env python3
from __future__ import annotations

import argparse
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from core.config import CONFIG
from core.logger import IRLogger
from modules.chain_of_custody import compress_collection, generate_chain_of_custody
from modules.filesystem_artifacts import (
    collect_filesystem_artifacts,
    collect_log_artifacts,
    collect_system_artifacts,
    collect_user_artifacts,
)
from modules.volatile_data import (
    collect_memory_dump,
    collect_network_connections,
    collect_process_list,
    collect_system_state,
)
from utils.validation import check_disk_space, is_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Linux IR triage collection tool")
    parser.add_argument("--output-location", help="Directory where collection output will be written")
    parser.add_argument("--skip-memory", action="store_true", help="Skip memory acquisition")
    parser.add_argument("--quick-mode", action="store_true", help="Skip heavier user and log artifact collection")
    parser.add_argument("--compress", action="store_true", help="Force ZIP archive creation")
    parser.add_argument("--no-compress", action="store_true", help="Disable ZIP archive creation")
    return parser.parse_args()


def start_collection() -> int:
    args = parse_args()
    output_root = Path(args.output_location).expanduser().resolve() if args.output_location else CONFIG["output_path"]
    logger = IRLogger(CONFIG["log_path"])

    print("\n=== Linux IR Triage Collection Tool ===")
    print(f"Starting collection at {datetime.now().astimezone().isoformat()}\n")

    if not is_root():
        logger.log("Root privileges are recommended. Some artifacts may be unavailable.", "WARNING")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collection_path = output_root / f"{timestamp}_{socket.gethostname()}"
    collection_path.mkdir(parents=True, exist_ok=True)
    logger.log(f"Output directory: {collection_path}", "INFO")

    if not check_disk_space(collection_path, CONFIG["required_free_gb"], logger):
        return 1

    metadata = {
        "StartTime": datetime.now(timezone.utc).isoformat(),
        "Modules": [],
        "QuickMode": args.quick_mode,
    }
    max_file_bytes = int(CONFIG["max_copy_file_mb"]) * 1024 * 1024

    try:
        if not args.skip_memory and CONFIG["collect_memory"]:
            result = collect_memory_dump(collection_path, CONFIG["tools_path"], logger)
            metadata["Modules"].append({"Name": "Memory", "Result": result})

        if CONFIG["collect_volatile_data"]:
            collect_process_list(collection_path, logger)
            collect_network_connections(collection_path, logger)
            collect_system_state(collection_path, logger)
            metadata["Modules"].append("Volatile Data")

        if CONFIG["collect_system_artifacts"]:
            collect_system_artifacts(collection_path, logger, max_file_bytes)
            metadata["Modules"].append("System Artifacts")

        if CONFIG["collect_log_artifacts"] and not args.quick_mode:
            collect_log_artifacts(collection_path, logger, max_file_bytes)
            metadata["Modules"].append("Log Artifacts")

        if CONFIG["collect_user_artifacts"] and not args.quick_mode:
            collect_user_artifacts(collection_path, logger, max_file_bytes)
            metadata["Modules"].append("User Artifacts")

        if CONFIG["collect_filesystem_artifacts"]:
            collect_filesystem_artifacts(collection_path, logger)
            metadata["Modules"].append("Filesystem Artifacts")

        end_time = datetime.now(timezone.utc)
        metadata["EndTime"] = end_time.isoformat()
        started = datetime.fromisoformat(metadata["StartTime"])
        metadata["DurationMinutes"] = round((end_time - started).total_seconds() / 60, 2)

        generate_chain_of_custody(collection_path, metadata, CONFIG["hash_algorithm"], logger)

        should_compress = args.compress or (CONFIG["compress"] and not args.no_compress)
        if should_compress:
            compress_collection(collection_path, logger)

        print("\n=== Collection Complete ===")
        print(f"Total time: {metadata['DurationMinutes']} minutes")
        print(f"Output: {collection_path}")
        return 0
    except Exception as exc:
        logger.log(f"Collection failed: {exc}", "ERROR")
        raise


if __name__ == "__main__":
    raise SystemExit(start_collection())
