from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG = {
    "collection_name": "IR-Triage-Collection",
    "output_path": BASE_DIR / "output",
    "log_path": BASE_DIR / "logs",
    "tools_path": BASE_DIR / "tools",
    "collect_memory": False,
    "collect_volatile_data": True,
    "collect_system_artifacts": True,
    "collect_user_artifacts": True,
    "collect_filesystem_artifacts": True,
    "compress": True,
    "hash_algorithm": "sha256",
    "required_free_gb": 3,
    "max_copy_file_mb": 100,
}

