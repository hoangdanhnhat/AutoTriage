import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser
from app.models.node import Node
from app.models.triage import TriageJob, NodeTriageStatus
from app.schemas.triage import TriageJobCreate, TriageJobOut, TriageJobDetail, NodeTriageStatusOut
from app.services.ansible_runner import run_triage_job

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/jobs", response_model=TriageJobOut, status_code=status.HTTP_201_CREATED)
async def create_job(payload: TriageJobCreate, db: DB, current_user: CurrentUser):
    # Validate nodes exist
    nodes_result = await db.execute(
        select(Node).where(Node.id.in_(payload.selected_node_ids))
    )
    found = nodes_result.scalars().all()
    if len(found) != len(payload.selected_node_ids):
        raise HTTPException(status_code=400, detail="One or more node IDs not found")

    job = TriageJob(
        name=payload.name,
        inventory_id=payload.inventory_id,
        selected_nodes=payload.selected_node_ids,
        selected_modules=payload.selected_modules.model_dump(),
        status="pending",
        created_by=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/start", response_model=TriageJobOut)
async def start_job(job_id: int, background_tasks: BackgroundTasks, db: DB, current_user: CurrentUser):
    result = await db.execute(select(TriageJob).where(TriageJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Job is already in status '{job.status}', cannot start",
        )
    # Run the playbook in the background
    background_tasks.add_task(run_triage_job, job_id)
    return job


@router.get("/jobs", response_model=list[TriageJobOut])
async def list_jobs(db: DB, current_user: CurrentUser):
    result = await db.execute(select(TriageJob).order_by(TriageJob.created_at.desc()))
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=TriageJobDetail)
async def get_job(job_id: int, db: DB, current_user: CurrentUser):
    result = await db.execute(select(TriageJob).where(TriageJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    ns_result = await db.execute(
        select(NodeTriageStatus)
        .where(NodeTriageStatus.job_id == job_id)
        .order_by(NodeTriageStatus.id)
    )
    node_statuses = ns_result.scalars().all()

    detail = TriageJobDetail(
        id=job.id,
        name=job.name,
        inventory_id=job.inventory_id,
        selected_nodes=job.selected_nodes,
        selected_modules=job.selected_modules,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        artifact_dir=job.artifact_dir,
        node_statuses=[NodeTriageStatusOut.model_validate(ns) for ns in node_statuses],
    )
    return detail
