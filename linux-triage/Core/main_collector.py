#!/usr/bin/env python3
"""
Main IR Triage Collector — Linux
Mirrors Core/MainCollector.ps1 (Start-IRCollection)

Usage:
    sudo python3 main_collector.py
    sudo python3 main_collector.py -o /mnt/usb/output
    sudo python3 main_collector.py --no-compress
    sudo python3 main_collector.py --skip-memory --quick
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the linux-triage root is on the Python path regardless of cwd
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR   = os.path.dirname(_SCRIPT_DIR)   # linux-triage/
sys.path.insert(0, _ROOT_DIR)

# ---------------------------------------------------------------------------
# Core imports
# ---------------------------------------------------------------------------
from Core.config import CONFIG
from Core.logger import log_ir, set_log_path
from Utils.validation import check_root, check_disk_space

# Module imports
from Modules.volatile_data import (
    collect_memory_dump,
    collect_process_list,
    collect_network_connections,
    collect_arp_routing,
    collect_logged_users,
)
from Modules.system_artifacts import (
    collect_logs,
    collect_etc,
    collect_proc_info,
)
from Modules.persistence_artifacts import (
    collect_cron,
    collect_systemd,
    collect_init,
    collect_suid_files,
    collect_third_party,
)
from Modules.user_artifacts import collect_user_artifacts
from Modules.chain_of_custody import generate_chain_of_custody, compress_collection


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Linux IR Triage Collection Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o", "--output",
        default=CONFIG["output_path"],
        help=f"Base output directory (default: {CONFIG['output_path']})",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Skip compressing the collection archive",
    )
    parser.add_argument(
        "--skip-memory",
        action="store_true",
        help="Skip memory acquisition even if collect_memory is enabled in config",
    )
    parser.add_argument(
        "-q", "--quick",
        action="store_true",
        help="Quick mode: skip slow operations (SUID scan, full log copy)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main collection orchestration  (mirrors Start-IRCollection)
# ---------------------------------------------------------------------------

def start_ir_collection() -> None:
    args = _parse_args()

    print("\n=== IR Triage Collection Tool (Linux) ===")

    # --- Pre-flight checks ---
    if not check_root():
        sys.exit(1)

    # --- Create output directory ---
    import socket
    from datetime import datetime
    timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
    hostname       = socket.gethostname()
    collection_path = os.path.join(args.output, f"{timestamp}_{hostname}")
    os.makedirs(collection_path, exist_ok=True)

    # --- Create log directory and activate logger ---
    log_dir = CONFIG["log_path"]
    os.makedirs(log_dir, exist_ok=True)
    set_log_path(log_dir)

    log_ir(f"Output directory: {collection_path}", level="INFO")

    # --- Disk space check ---
    if not check_disk_space(collection_path, required_gb=10):
        sys.exit(1)

    # --- Merge CLI flags into effective config ---
    effective_compress = not args.no_compress and CONFIG["compress"]
    effective_memory   = not args.skip_memory and CONFIG["collect_memory"]

    # --- Collection metadata (mirrors $collectionMetadata) ---
    start_time = datetime.now()
    collection_metadata: dict = {
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "hostname":   hostname,
        "modules":    [],
    }

    try:
        # 1. Memory (most volatile — mirrors first step in MainCollector.ps1)
        if effective_memory:
            mem_result = collect_memory_dump(collection_path)
            collection_metadata["modules"].append({
                "name": "Memory", "result": mem_result
            })

        # 2. Volatile data: processes, network, users, ARP/routing
        if CONFIG["collect_volatile"]:
            collect_process_list(collection_path)
            collect_network_connections(collection_path)
            collect_logged_users(collection_path)
            collect_arp_routing(collection_path)
            collection_metadata["modules"].append("Volatile Data")

        # 3. System artifacts: /var/log/, /etc/, /proc/
        if CONFIG["collect_system"]:
            if not args.quick:
                collect_logs(collection_path)
            else:
                log_ir("Quick mode: skipping full /var/log/ copy", level="WARNING")
            collect_etc(collection_path)
            collect_proc_info(collection_path)
            collection_metadata["modules"].append("System Artifacts")

        # 4. Persistence artifacts: cron, systemd, init, SUID, 3rd-party
        if CONFIG["collect_persistence"]:
            collect_cron(collection_path)
            collect_systemd(collection_path)
            collect_init(collection_path)
            if not args.quick:
                collect_suid_files(collection_path)
            else:
                log_ir("Quick mode: skipping SUID/SGID scan", level="WARNING")
            collect_third_party(collection_path)
            collection_metadata["modules"].append("Persistence Artifacts")

        # 5. User artifacts: history, SSH, browsers, dotfiles
        if CONFIG["collect_user"]:
            collect_user_artifacts(collection_path)
            collection_metadata["modules"].append("User Artifacts")

        # 6. Chain of custody (hash manifest + system metadata)
        end_time  = datetime.now()
        duration  = round((end_time - start_time).total_seconds() / 60, 2)
        collection_metadata["end_time"]        = end_time.strftime("%Y-%m-%d %H:%M:%S")
        collection_metadata["duration_minutes"] = duration

        generate_chain_of_custody(collection_path, collection_metadata)

        # 7. Compress
        if effective_compress:
            compress_collection(collection_path)

        print("\n=== Collection Complete ===")
        print(f"Total time : {duration} minutes")
        print(f"Output     : {collection_path}")

    except Exception as exc:
        log_ir(f"Collection failed: {exc}", level="ERROR")
        raise


if __name__ == "__main__":
    start_ir_collection()
