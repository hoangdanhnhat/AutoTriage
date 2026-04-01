from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_content = Column(Text, nullable=False)
    parsed_data = Column(JSONB)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
