"""
Chain of Custody & Compression — Linux equivalent of Modules/ChainOfCustody.ps1

  - generate_chain_of_custody()  hashes every collected file (SHA-256) and
    writes ChainOfCustody.json with system metadata + file integrity manifest.
  - compress_collection()        creates a .tar.gz archive of the output
    directory and logs its hash (mirrors Compress-Collection).
"""

import hashlib
import json
import os
import platform
import socket
import subprocess
import tarfile
from datetime import datetime, timezone

from Core.config import CONFIG
from Core.logger import log_ir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _sha256(file_path: str) -> str:
    """Return the SHA-256 hex digest of *file_path*."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Chain of custody  (mirrors New-ChainOfCustody)
# ---------------------------------------------------------------------------

def generate_chain_of_custody(output_path: str, collection_metadata: dict) -> None:
    """
    Walk *output_path*, hash every file, gather system metadata, and write
    ChainOfCustody.json — mirrors New-ChainOfCustody in ChainOfCustody.ps1.
    """
    log_ir("Generating chain of custody documentation...")

    # --- System information (mirrors SystemInformation block) ---
    system_info = {
        "os_version":    platform.platform(),
        "kernel":        platform.release(),
        "architecture":  platform.machine(),
        "hostname":      socket.getfqdn(),
        "timezone":      _run(["timedatectl", "show", "--property=Timezone", "--value"])
                         or _run(["date", "+%Z"]),
        "uptime":        _run(["uptime", "-p"]),
        "ip_addresses":  _run(["hostname", "-I"]).split(),
    }

    # --- Case / collection information (mirrors CaseInformation block) ---
    import uuid
    case_info = {
        "collection_id":   str(uuid.uuid4()),
        "timestamp":       datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "collector":       os.environ.get("SUDO_USER") or os.environ.get("USER") or "root",
        "system_name":     socket.gethostname(),
        "ip_addresses":    system_info["ip_addresses"],
    }

    # --- File integrity manifest (mirrors FileIntegrity block) ---
    log_ir("Hashing all collected files...")
    file_integrity: dict[str, dict] = {}
    file_count = 0

    for root, _dirs, files in os.walk(output_path):
        for fname in files:
            # Skip the chain-of-custody file itself
            if fname == "ChainOfCustody.json":
                continue
            full_path = os.path.join(root, fname)
            rel_path  = os.path.relpath(full_path, output_path)
            try:
                stat = os.stat(full_path)
                file_integrity[rel_path] = {
                    "hash_sha256": _sha256(full_path),
                    "size_bytes":  stat.st_size,
                    "modified":    datetime.fromtimestamp(stat.st_mtime,
                                                          timezone.utc
                                                         ).strftime("%Y-%m-%d %H:%M:%S UTC"),
                }
                file_count += 1
            except OSError:
                pass

    custody = {
        "case_information":   case_info,
        "system_information": system_info,
        "collection_details": collection_metadata,
        "file_integrity":     file_integrity,
    }

    coc_path = os.path.join(output_path, "ChainOfCustody.json")
    with open(coc_path, "w", encoding="utf-8") as fh:
        json.dump(custody, fh, indent=2)

    log_ir(
        f"Chain of custody complete — {file_count} files hashed → {coc_path}",
        level="SUCCESS",
    )


# ---------------------------------------------------------------------------
# Compression  (mirrors Compress-Collection)
# ---------------------------------------------------------------------------

def compress_collection(source_path: str) -> str | None:
    """
    Create a .tar.gz archive of *source_path* and log its SHA-256 hash.
    Returns the archive path on success, None on failure.
    Mirrors Compress-Collection which uses ZipFile in ChainOfCustody.ps1.
    """
    log_ir("Compressing collection...")

    archive_path = f"{source_path}.tar.gz"

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_path, arcname=os.path.basename(source_path))

        size_gb = round(os.path.getsize(archive_path) / (1024 ** 3), 3)
        archive_hash = _sha256(archive_path)

        log_ir(f"Archive created: {archive_path} ({size_gb} GB)", level="SUCCESS")
        log_ir(f"Archive hash (SHA256): {archive_hash}", level="INFO")

        return archive_path

    except Exception as exc:
        log_ir(f"Failed to compress collection: {exc}", level="ERROR")
        log_ir(f"Collection data is still available at: {source_path}", level="WARNING")
        return None
