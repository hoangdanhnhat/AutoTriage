from __future__ import annotations

import getpass
import hashlib
import json
import platform
import shutil
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path


def generate_chain_of_custody(output_path: Path, collection_metadata: dict, hash_algorithm: str, logger) -> Path:
    logger.log("Generating chain of custody documentation...")
    custody = {
        "CaseInformation": {
            "CollectionID": str(uuid.uuid4()),
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Collector": getpass.getuser(),
            "SystemName": socket.gethostname(),
            "SystemIP": _get_ip_addresses(),
        },
        "SystemInformation": {
            "OSVersion": platform.platform(),
            "Kernel": platform.release(),
            "Architecture": platform.machine(),
            "TimeZone": datetime.now().astimezone().tzname(),
            "LastBootTime": _read_boot_time(),
        },
        "CollectionDetails": collection_metadata,
        "FileIntegrity": {},
    }

    for file_path in sorted(output_path.rglob("*")):
        if not file_path.is_file() or file_path.name == "ChainOfCustody.json":
            continue
        relative = str(file_path.relative_to(output_path))
        stat = file_path.stat()
        custody["FileIntegrity"][relative] = {
            "Hash": hash_file(file_path, hash_algorithm),
            "Size": stat.st_size,
            "Created": datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
            "Modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        }

    custody_path = output_path / "ChainOfCustody.json"
    custody_path.write_text(json.dumps(custody, indent=2, default=str), encoding="utf-8")
    logger.log("Chain of custody documentation complete", "SUCCESS")
    return custody_path


def compress_collection(source_path: Path, logger) -> Path | None:
    logger.log("Compressing collection...", "INFO")
    archive_base = source_path.with_suffix("")
    archive_path = Path(shutil.make_archive(str(archive_base), "zip", root_dir=source_path))
    if archive_path.exists():
        size_gb = round(archive_path.stat().st_size / (1024**3), 2)
        archive_hash = hash_file(archive_path, "sha256")
        logger.log(f"Archive created: {archive_path} ({size_gb} GB)", "SUCCESS")
        logger.log(f"Archive hash (SHA256): {archive_hash}", "INFO")
        return archive_path
    logger.log(f"Failed to create archive for {source_path}", "ERROR")
    return None


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _get_ip_addresses() -> list[str]:
    addresses = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(info[4][0])
    except socket.gaierror:
        pass
    return sorted(address for address in addresses if not address.startswith("127."))


def _read_boot_time() -> str | None:
    try:
        for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
            if line.startswith("btime "):
                return datetime.fromtimestamp(int(line.split()[1]), timezone.utc).isoformat()
    except Exception:
        return None
    return None

