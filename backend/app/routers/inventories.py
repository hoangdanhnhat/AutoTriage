from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser
from app.models.inventory import Inventory
from app.models.node import Node, NodeStatus
from app.schemas.inventory import InventoryOut, InventoryDetail
from app.schemas.node import NodeWithStatus
from app.services.host_resolution import normalize_host_identity
from app.services.inventory_parser import parse_inventory, flatten_nodes

router = APIRouter(prefix="/inventories", tags=["inventories"])


@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
async def create_inventory(
    db: DB,
    current_user: CurrentUser,
    name: str = Form(...),
    file: UploadFile = File(...),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    parsed = parse_inventory(content)
    inv = Inventory(
        name=name,
        file_content=content,
        parsed_data=parsed,
        created_by=current_user.id,
    )
    db.add(inv)
    await db.flush()  # get inv.id

    # Persist nodes
    nodes_flat = flatten_nodes(parsed)
    for n_data in nodes_flat:
        node = Node(
            inventory_id=inv.id,
            ip_address=n_data["ip_address"],
            hostname=n_data.get("hostname"),
            ansible_user=n_data.get("ansible_user"),
            ansible_connection=n_data.get("ansible_connection", "ssh"),
            ansible_shell_type=n_data.get("ansible_shell_type", "powershell"),
            group_name=n_data.get("group_name"),
            extra_vars=n_data.get("extra_vars") or {},
        )
        db.add(node)

    await db.commit()
    await db.refresh(inv)
    return inv


@router.get("", response_model=list[InventoryOut])
async def list_inventories(db: DB, current_user: CurrentUser):
    result = await db.execute(select(Inventory).order_by(Inventory.created_at.desc()))
    return result.scalars().all()


@router.get("/{inv_id}", response_model=InventoryDetail)
async def get_inventory(inv_id: int, db: DB, current_user: CurrentUser):
    inv = await _get_or_404(db, inv_id)
    return InventoryDetail(
        id=inv.id,
        name=inv.name,
        parsed_data=_resolved_parsed_data(inv.parsed_data),
        created_by=inv.created_by,
        created_at=inv.created_at,
        file_content=inv.file_content,
    )


@router.delete("/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory(inv_id: int, db: DB, current_user: CurrentUser):
    inv = await _get_or_404(db, inv_id)
    await db.delete(inv)
    await db.commit()


@router.get("/{inv_id}/nodes", response_model=list[NodeWithStatus])
async def get_inventory_nodes(inv_id: int, db: DB, current_user: CurrentUser):
    await _get_or_404(db, inv_id)
    result = await db.execute(select(Node).where(Node.inventory_id == inv_id))
    nodes = result.scalars().all()

    # Attach latest status for each node
    node_ids = [n.id for n in nodes]
    statuses: dict[int, NodeStatus] = {}
    if node_ids:
        s_result = await db.execute(select(NodeStatus).where(NodeStatus.node_id.in_(node_ids)))
        for ns in s_result.scalars().all():
            statuses[ns.node_id] = ns

    output = []
    for n in nodes:
        ns = statuses.get(n.id)
        ip_address, hostname = normalize_host_identity(n.ip_address, n.hostname)
        output.append(
            NodeWithStatus(
                id=n.id,
                inventory_id=n.inventory_id,
                ip_address=ip_address,
                hostname=hostname,
                ansible_user=n.ansible_user,
                ansible_connection=n.ansible_connection,
                ansible_shell_type=n.ansible_shell_type,
                group_name=n.group_name,
                extra_vars=n.extra_vars,
                status=ns.status if ns else "unknown",
                last_checked=ns.last_checked if ns else None,
            )
        )
    return output


async def _get_or_404(db: AsyncSession, inv_id: int) -> Inventory:
    result = await db.execute(select(Inventory).where(Inventory.id == inv_id))
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inv


def _resolved_parsed_data(parsed_data):
    if not isinstance(parsed_data, dict):
        return parsed_data

    resolved = {
        **parsed_data,
        "groups": {},
    }
    for group_name, group_data in (parsed_data.get("groups") or {}).items():
        if not isinstance(group_data, dict):
            resolved["groups"][group_name] = group_data
            continue

        resolved_group = {
            **group_data,
            "nodes": [],
        }
        for node in group_data.get("nodes") or []:
            if not isinstance(node, dict) or not node.get("ip_address"):
                resolved_group["nodes"].append(node)
                continue
            ip_address, hostname = normalize_host_identity(
                node["ip_address"],
                node.get("hostname"),
            )
            resolved_group["nodes"].append({
                **node,
                "ip_address": ip_address,
                "hostname": hostname,
            })
        resolved["groups"][group_name] = resolved_group

    return resolved
