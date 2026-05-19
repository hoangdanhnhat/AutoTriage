"""
Generate per-job collector configuration files.
"""
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Template lives next to this file in the templates/ directory
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))
_TEMPLATE_NAME = "Config.ps1.j2"


def generate_config(job_id: int, modules: dict, output_dir: str) -> str:
    """
    Render Config.ps1 and write it to <output_dir>/Config_<job_id>.ps1.
    Returns the absolute path to the written file.

    modules dict keys:
      collect_memory, collect_volatile_data, collect_registry, collect_event_logs,
      collect_prefetch, collect_windows_artifacts, collect_user_artifacts,
      collect_program_data, collect_ntfs
    """
    template = _env.get_template(_TEMPLATE_NAME)
    rendered = template.render(
        collect_memory=modules.get("collect_memory", False),
        collect_volatile_data=modules.get("collect_volatile_data", True),
        collect_registry=modules.get("collect_registry", True),
        collect_event_logs=modules.get("collect_event_logs", True),
        collect_prefetch=modules.get("collect_prefetch", False),
        collect_windows_artifacts=modules.get("collect_windows_artifacts", True),
        collect_user_artifacts=modules.get("collect_user_artifacts", True),
        collect_program_data=modules.get("collect_program_data", True),
        collect_ntfs=modules.get("collect_ntfs", False),
    )
    os.makedirs(output_dir, exist_ok=True)
    dest_path = os.path.join(output_dir, f"Config_{job_id}.ps1")
    with open(dest_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    return dest_path


def _py_bool(value: bool) -> str:
    return "True" if value else "False"


def generate_linux_config(job_id: int, modules: dict, output_dir: str) -> str:
    """
    Render linux-triage/core/config.py for a job.
    Returns the absolute path to the written file.
    """
    rendered = f"""from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG = {{
    "collection_name": "IR-Triage-Collection",
    "output_path": BASE_DIR / "output",
    "log_path": BASE_DIR / "logs",
    "tools_path": BASE_DIR / "tools",
    "collect_memory": {_py_bool(modules.get("collect_linux_memory", modules.get("collect_memory", False)))},
    "collect_volatile_data": {_py_bool(modules.get("collect_linux_volatile_data", modules.get("collect_volatile_data", True)))},
    "collect_system_artifacts": {_py_bool(modules.get("collect_system_artifacts", True))},
    "collect_log_artifacts": {_py_bool(modules.get("collect_log_artifacts", True))},
    "collect_user_artifacts": {_py_bool(modules.get("collect_linux_user_artifacts", modules.get("collect_user_artifacts", True)))},
    "collect_filesystem_artifacts": {_py_bool(modules.get("collect_filesystem_artifacts", True))},
    "compress": True,
    "hash_algorithm": "sha256",
    "required_free_gb": 3,
    "max_copy_file_mb": 100,
}}
"""
    os.makedirs(output_dir, exist_ok=True)
    dest_path = os.path.join(output_dir, f"linux_config_{job_id}.py")
    with open(dest_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    return dest_path
