from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class InventoryCreate(BaseModel):
    name: str


class InventoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    parsed_data: Optional[Any] = None
    created_by: Optional[int] = None
    created_at: datetime


class InventoryDetail(InventoryOut):
    file_content: str
