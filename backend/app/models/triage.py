from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class TriageJob(Base):
    __tablename__ = "triage_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    inventory_id = Column(Integer, ForeignKey("inventories.id", ondelete="SET NULL"), nullable=True)
    # list of node IDs selected for this job
    selected_nodes = Column(JSONB, nullable=False)
    # dict of module flags  e.g. {"collect_memory": false, "collect_volatile_data": true, ...}
    selected_modules = Column(JSONB, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    artifact_dir = Column(String(500))


class NodeTriageStatus(Base):
    __tablename__ = "node_triage_statuses"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("triage_jobs.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(45), nullable=False)
    hostname = Column(String(255))
    status = Column(String(20), default="pending", nullable=False)  # pending/running/completed/failed/skipped
    output_log = Column(Text)
    artifact_path = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
