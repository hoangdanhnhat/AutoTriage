from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventories.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    hostname = Column(String(255))
    ansible_user = Column(String(100))
    ansible_connection = Column(String(50), default="ssh")
    ansible_shell_type = Column(String(50), default="powershell")
    group_name = Column(String(100))
    extra_vars = Column(JSONB)


class NodeStatus(Base):
    __tablename__ = "node_statuses"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(String(20), default="unknown", nullable=False)   # online / offline / unknown
    last_checked = Column(DateTime)
