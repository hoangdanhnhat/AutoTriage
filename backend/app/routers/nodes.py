from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser
from app.models.node import Node, NodeStatus
from app.schemas.node import NodeWithStatus, CheckStatusResponse
from app.services.node_checker import check_nodes

router = APIRouter(prefix="/inventories", tags=["nodes"])


@router.post("/{inv_id}/check-status", response_model=CheckStatusResponse)
async def check_inventory_status(inv_id: int, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Node).where(Node.inventory_id == inv_id))
    nodes = result.scalars().all()
    if not nodes:
        raise HTTPException(status_code=404, detail="No nodes found for this inventory")

    node_dicts = [
        {
            "id": n.id,
            "ip_address": n.ip_address,
            "hostname": n.hostname,
            "ansible_user": n.ansible_user,
            "ansible_connection": n.ansible_connection,
            "ansible_shell_type": n.ansible_shell_type,
            "group_name": n.group_name,
            "extra_vars": n.extra_vars,
        }
        for n in nodes
    ]

    checked = await check_nodes(node_dicts)

    # Upsert NodeStatus rows
    now = datetime.now(timezone.utc)
    results_out = []
    for item in checked:
        s_result = await db.execute(
            select(NodeStatus).where(NodeStatus.node_id == item["id"])
        )
        ns = s_result.scalar_one_or_none()
        if ns is None:
            ns = NodeStatus(node_id=item["id"], status=item["status"], last_checked=now)
            db.add(ns)
        else:
            ns.status = item["status"]
            ns.last_checked = now
        results_out.append(
            NodeWithStatus(
                id=item["id"],
                inventory_id=inv_id,
                ip_address=item["ip_address"],
                hostname=item.get("hostname"),
                ansible_user=item.get("ansible_user"),
                ansible_connection=item.get("ansible_connection"),
                ansible_shell_type=item.get("ansible_shell_type"),
                group_name=item.get("group_name"),
                extra_vars=item.get("extra_vars"),
                status=item["status"],
                last_checked=now,
            )
        )

    await db.commit()
    return CheckStatusResponse(checked=len(results_out), results=results_out)
