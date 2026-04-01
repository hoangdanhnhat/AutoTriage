"""
Check whether nodes are reachable by attempting a TCP connection to port 22 (SSH).
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

CONNECTION_TIMEOUT = 5.0   # seconds
SSH_PORT = 22


async def _check_single(ip: str) -> str:
    """Returns 'online' or 'offline'."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, SSH_PORT),
            timeout=CONNECTION_TIMEOUT,
        )
        writer.close()
        await writer.wait_closed()
        return "online"
    except Exception:
        return "offline"


async def check_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Takes a list of node dicts with at least 'ip_address'.
    Returns same list augmented with 'status' and 'last_checked'.
    """
    tasks = [_check_single(n["ip_address"]) for n in nodes]
    statuses = await asyncio.gather(*tasks)
    now = datetime.now(timezone.utc)
    result = []
    for node, status in zip(nodes, statuses):
        result.append({**node, "status": status, "last_checked": now})
    return result
