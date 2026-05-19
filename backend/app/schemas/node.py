from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class NodeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    inventory_id: int
    ip_address: str
    hostname: Optional[str] = None
    ansible_user: Optional[str] = None
    ansible_connection: Optional[str] = None
    ansible_shell_type: Optional[str] = None
    group_name: Optional[str] = None
    extra_vars: Optional[Any] = None


class NodeStatusOut(BaseModel):
    model_config = {"from_attributes": True}

    node_id: int
    status: str
    last_checked: Optional[datetime] = None


class NodeWithStatus(NodeOut):
    status: str = "unknown"
    last_checked: Optional[datetime] = None


class CheckStatusResponse(BaseModel):
    checked: int
    results: list[NodeWithStatus]
