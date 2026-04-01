from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ModuleSelection(BaseModel):
    collect_memory: bool = False
    collect_volatile_data: bool = True
    collect_registry: bool = True
    collect_event_logs: bool = True
    collect_prefetch: bool = False
    collect_windows_artifacts: bool = True
    collect_user_artifacts: bool = True
    collect_program_data: bool = True
    collect_ntfs: bool = False


class TriageJobCreate(BaseModel):
    name: str
    inventory_id: Optional[int] = None
    selected_node_ids: list[int]
    selected_modules: ModuleSelection


class NodeTriageStatusOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    job_id: int
    node_id: Optional[int] = None
    ip_address: str
    hostname: Optional[str] = None
    status: str
    output_log: Optional[str] = None
    artifact_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TriageJobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    inventory_id: Optional[int] = None
    selected_nodes: Any
    selected_modules: Any
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    artifact_dir: Optional[str] = None


class TriageJobDetail(TriageJobOut):
    node_statuses: list[NodeTriageStatusOut] = []
