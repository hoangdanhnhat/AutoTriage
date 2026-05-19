"""
Ansible runner service.

Orchestrates a triage job:
1. Write a dynamic inventory file for the selected nodes.
2. Generate Config.ps1 via config_generator.
3. Launch ansible-playbook (auto-triage-web.yml) as an async subprocess.
4. Stream stdout line-by-line; parse per-host task progress.
5. Publish WS events to Redis pub/sub channel `triage:<job_id>`.
6. Update DB: node_triage_statuses + triage_jobs.
"""
import asyncio
import json
import logging
import os
import re
import shlex
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.triage import TriageJob, NodeTriageStatus
from app.services.config_generator import generate_config, generate_linux_config
from app.utils.time import utc_now_naive

logger = logging.getLogger(__name__)

PLAYBOOK_PATH = "/app/Ansible/auto-triage-web.yml"

# Patterns to detect per-host Ansible output lines
_TASK_RE = re.compile(r"^TASK \[(.+?)\]")
_OK_RE = re.compile(r"^ok:\s+\[([^\]]+)\]")
_CHANGED_RE = re.compile(r"^changed:\s+\[([^\]]+)\]")
_FATAL_RE = re.compile(r"^fatal:\s+\[([^\]]+)\]")
_SKIPPING_RE = re.compile(r"^skipping:\s+\[([^\]]+)\]")
_PLAY_RECAP_RE = re.compile(r"^PLAY RECAP")


def _ps_bool(value: bool) -> str:
    return "$true" if value else "$false"


def _write_dynamic_inventory(nodes: list[dict[str, Any]], path: str) -> None:
    """Write a minimal Ansible INI inventory for the given nodes."""
    grouped_nodes = {
        "windows_nodes": [],
        "linux_nodes": [],
    }
    for n in nodes:
        group_name = (n.get("group_name") or "").lower()
        if "linux" in group_name:
            grouped_nodes["linux_nodes"].append(n)
        else:
            grouped_nodes["windows_nodes"].append(n)

    lines = []
    for group, group_nodes in grouped_nodes.items():
        lines.append(f"[{group}]")
        for n in group_nodes:
            lines.append(_inventory_host_line(n, group))
        lines.append("")

    lines += [
        "[triage_targets:children]",
        "windows_nodes",
        "linux_nodes",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def _inventory_host_line(node: dict[str, Any], group: str) -> str:
    """Render one host line while avoiding Windows-only defaults on Linux hosts."""
    ip = node["ip_address"]
    user = node.get("ansible_user")
    conn = node.get("ansible_connection") or "ssh"
    shell = node.get("ansible_shell_type")
    extra = node.get("extra_vars") or {}

    parts = [ip]
    if user:
        parts.append(f"ansible_user={_inventory_value(user)}")
    elif group == "linux_nodes" and settings.linux_ansible_user:
        parts.append(f"ansible_user={_inventory_value(settings.linux_ansible_user)}")
    elif group == "windows_nodes":
        parts.append("ansible_user=Administrator")
    if conn:
        parts.append(f"ansible_connection={conn}")
    if conn == "ssh":
        parts.append("ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'")
    if group == "linux_nodes" and settings.linux_become_password:
        parts.append("ansible_become=true")
        parts.append("ansible_become_method=sudo")
        parts.append(f"ansible_become_password={_inventory_value(settings.linux_become_password)}")
    if shell and (group == "windows_nodes" or shell != "powershell"):
        parts.append(f"ansible_shell_type={shell}")
    parts.extend(f"{k}={v}" for k, v in extra.items())
    return " ".join(parts)


def _inventory_value(value: str) -> str:
    return shlex.quote(str(value))


async def _publish(redis_client, channel: str, event: dict) -> None:
    try:
        await redis_client.publish(channel, json.dumps(event))
    except Exception as exc:
        logger.warning("Redis publish failed: %s", exc)


async def run_triage_job(job_id: int) -> None:
    """
    Entry point called from a background task.
    Creates its own DB session and Redis connection so it can run independently.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

    async with session_factory() as db:
        try:
            await _execute_job(job_id, db, redis_client)
        except Exception as exc:
            logger.exception("Unhandled error in triage job %d: %s", job_id, exc)
            await db.execute(
                update(TriageJob)
                .where(TriageJob.id == job_id)
                .values(status="failed", completed_at=utc_now_naive())
            )
            await db.commit()
            channel = f"triage:{job_id}"
            await _publish(redis_client, channel, {"type": "job_status", "status": "failed"})
        finally:
            await redis_client.aclose()
            await engine.dispose()


async def _execute_job(job_id: int, db: AsyncSession, redis_client) -> None:
    channel = f"triage:{job_id}"

    # ── Load job ───────────────────────────────────────────────────────────────
    result = await db.execute(select(TriageJob).where(TriageJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    # Load node details from DB
    from app.models.node import Node
    node_ids: list[int] = job.selected_nodes
    nodes_result = await db.execute(select(Node).where(Node.id.in_(node_ids)))
    db_nodes = nodes_result.scalars().all()
    nodes = [
        {
            "id": n.id,
            "ip_address": n.ip_address,
            "hostname": n.hostname or n.ip_address,
            "ansible_user": n.ansible_user,
            "ansible_connection": n.ansible_connection or "ssh",
            "ansible_shell_type": n.ansible_shell_type,
            "group_name": n.group_name,
            "extra_vars": n.extra_vars or {},
        }
        for n in db_nodes
    ]

    # ── Prepare output directory ───────────────────────────────────────────────
    artifact_dir = os.path.join(settings.artifacts_dir, str(job_id))
    os.makedirs(artifact_dir, exist_ok=True)

    # ── Generate Config.ps1 ────────────────────────────────────────────────────
    modules: dict = job.selected_modules
    config_path = generate_config(job_id, modules, artifact_dir)
    linux_config_path = generate_linux_config(job_id, modules, artifact_dir)

    # ── Write dynamic inventory ────────────────────────────────────────────────
    inv_file = os.path.join(artifact_dir, "inventory.ini")
    _write_dynamic_inventory(nodes, inv_file)

    # ── Mark job as running ────────────────────────────────────────────────────
    await db.execute(
        update(TriageJob)
        .where(TriageJob.id == job_id)
        .values(status="running", started_at=utc_now_naive(), artifact_dir=artifact_dir)
    )
    # Create NodeTriageStatus rows for each node
    for n in nodes:
        nts = NodeTriageStatus(
            job_id=job_id,
            node_id=n["id"],
            ip_address=n["ip_address"],
            hostname=n["hostname"],
            status="pending",
        )
        db.add(nts)
    await db.commit()

    await _publish(redis_client, channel, {
        "type": "job_status",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # ── Build ansible-playbook command ─────────────────────────────────────────
    cmd = [
        "ansible-playbook",
        PLAYBOOK_PATH,
        "-i", inv_file,
        "--private-key", settings.ansible_ssh_key_path,
        "--extra-vars",
        json.dumps({
            "job_id": str(job_id),
            "artifact_base_dir": artifact_dir,
            "config_ps1_path": config_path,
            "linux_config_path": linux_config_path,
        }),
    ]

    logger.info("Launching: %s", " ".join(cmd))

    # ── Launch subprocess ──────────────────────────────────────────────────────
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "ANSIBLE_FORCE_COLOR": "false", "ANSIBLE_NOCOLOR": "1"},
    )

    current_task_name = "initializing"
    ip_log_buffer: dict[str, list[str]] = {n["ip_address"]: [] for n in nodes}
    node_started: dict[str, bool] = {n["ip_address"]: False for n in nodes}

    # ── Stream output ──────────────────────────────────────────────────────────
    assert proc.stdout is not None
    in_recap = False

    async for raw in proc.stdout:
        line = raw.decode(errors="replace").rstrip()
        logger.debug("[ansible] %s", line)

        if _PLAY_RECAP_RE.match(line):
            in_recap = True
            continue

        # Detect task name
        m = _TASK_RE.match(line)
        if m:
            current_task_name = m.group(1).strip()
            continue

        # ok / changed per host
        for pattern, new_status in [(_OK_RE, None), (_CHANGED_RE, None)]:
            m = pattern.match(line)
            if m:
                ip = _resolve_ip(m.group(1), nodes)
                if ip:
                    if not node_started[ip]:
                        node_started[ip] = True
                        await _update_node_status(db, job_id, ip, "running",
                                                   started_at=utc_now_naive())
                    ip_log_buffer[ip].append(f"[{current_task_name}] ok")
                    await _publish(redis_client, channel, {
                        "type": "node_status",
                        "node_ip": ip,
                        "status": "running",
                        "task": current_task_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    await _publish(redis_client, channel, {
                        "type": "log",
                        "node_ip": ip,
                        "line": f"[{current_task_name}] ok",
                    })
                break

        # fatal
        m = _FATAL_RE.match(line)
        if m:
            ip = _resolve_ip(m.group(1), nodes)
            if ip:
                ip_log_buffer[ip].append(f"[{current_task_name}] FAILED: {line}")
                await _publish(redis_client, channel, {
                    "type": "node_status",
                    "node_ip": ip,
                    "status": "failed",
                    "task": current_task_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                await _publish(redis_client, channel, {
                    "type": "log",
                    "node_ip": ip,
                    "line": f"[{current_task_name}] FAILED",
                })
                await _update_node_status(
                    db, job_id, ip, "failed",
                    log="\n".join(ip_log_buffer[ip]),
                    error_message=line,
                    completed_at=utc_now_naive(),
                )

    await proc.wait()

    # ── Parse RECAP and finalize ────────────────────────────────────────────────
    # Any node still in "running" or "pending" → completed (ansible exit 0 = success)
    final_job_status = "completed" if proc.returncode == 0 else "partial"

    for n in nodes:
        ip = n["ip_address"]
        # Check current DB status
        res = await db.execute(
            select(NodeTriageStatus)
            .where(NodeTriageStatus.job_id == job_id, NodeTriageStatus.ip_address == ip)
        )
        nts = res.scalar_one_or_none()
        if nts and nts.status in ("pending", "running"):
            new_s = "completed" if proc.returncode == 0 else "failed"
            artifact_zip = _find_artifact_zip(artifact_dir, ip)
            await _update_node_status(
                db, job_id, ip, new_s,
                log="\n".join(ip_log_buffer.get(ip, [])),
                artifact_path=artifact_zip,
                completed_at=utc_now_naive(),
            )
            await _publish(redis_client, channel, {
                "type": "node_status",
                "node_ip": ip,
                "status": new_s,
                "task": "done",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    await db.execute(
        update(TriageJob)
        .where(TriageJob.id == job_id)
        .values(status=final_job_status, completed_at=utc_now_naive())
    )
    await db.commit()

    await _publish(redis_client, channel, {
        "type": "job_status",
        "status": final_job_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def _resolve_ip(host_token: str, nodes: list[dict]) -> str | None:
    """Match Ansible [host_token] back to an IP address."""
    host_token = host_token.split(" ")[0]  # strip trailing metadata
    for n in nodes:
        if host_token == n["ip_address"] or host_token == n.get("hostname"):
            return n["ip_address"]
    return None


def _find_artifact_zip(artifact_dir: str, ip: str) -> str | None:
    """Look for a fetched Linux or Windows artifact under artifact_dir."""
    base = Path(artifact_dir)
    host_base = base / ip
    search_base = host_base if host_base.exists() else base
    candidates = [
        candidate
        for pattern in ("*.zip", "*.tar.gz", "*.tar")
        for candidate in search_base.rglob(pattern)
    ]
    if candidates:
        return str(sorted(candidates)[0])
    return None


async def _update_node_status(
    db: AsyncSession,
    job_id: int,
    ip: str,
    status: str,
    log: str | None = None,
    error_message: str | None = None,
    artifact_path: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> None:
    values: dict = {"status": status}
    if log is not None:
        values["output_log"] = log
    if error_message is not None:
        values["error_message"] = error_message
    if artifact_path is not None:
        values["artifact_path"] = artifact_path
    if started_at is not None:
        values["started_at"] = started_at
    if completed_at is not None:
        values["completed_at"] = completed_at
    await db.execute(
        update(NodeTriageStatus)
        .where(NodeTriageStatus.job_id == job_id, NodeTriageStatus.ip_address == ip)
        .values(**values)
    )
    await db.commit()
