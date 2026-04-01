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
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.triage import TriageJob, NodeTriageStatus
from app.services.config_generator import generate_config

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
    lines = ["[triage_targets]"]
    for n in nodes:
        ip = n["ip_address"]
        user = n.get("ansible_user", "Administrator")
        conn = n.get("ansible_connection", "ssh")
        shell = n.get("ansible_shell_type", "powershell")
        extra = n.get("extra_vars") or {}
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        lines.append(
            f"{ip} ansible_user={user} ansible_connection={conn} "
            f"ansible_shell_type={shell} {extra_str}".strip()
        )
    lines += [
        "",
        "[triage_targets:vars]",
        "ansible_connection=ssh",
        "ansible_shell_type=powershell",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


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
                .values(status="failed", completed_at=datetime.now(timezone.utc))
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
            "ansible_user": n.ansible_user or "Administrator",
            "ansible_connection": n.ansible_connection or "ssh",
            "ansible_shell_type": n.ansible_shell_type or "powershell",
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

    # ── Write dynamic inventory ────────────────────────────────────────────────
    inv_file = os.path.join(artifact_dir, "inventory.ini")
    _write_dynamic_inventory(nodes, inv_file)

    # ── Mark job as running ────────────────────────────────────────────────────
    await db.execute(
        update(TriageJob)
        .where(TriageJob.id == job_id)
        .values(status="running", started_at=datetime.now(timezone.utc), artifact_dir=artifact_dir)
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
                                                   started_at=datetime.now(timezone.utc))
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
                    completed_at=datetime.now(timezone.utc),
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
                completed_at=datetime.now(timezone.utc),
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
        .values(status=final_job_status, completed_at=datetime.now(timezone.utc))
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
    """Look for the fetched ZIP under artifact_dir/<ip>/."""
    base = Path(artifact_dir)
    candidates = list(base.rglob("*.zip"))
    if candidates:
        return str(candidates[0])
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
