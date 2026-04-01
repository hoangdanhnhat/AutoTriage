import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import DB, CurrentUser
from app.models.triage import TriageJob
from sqlalchemy import select

router = APIRouter(prefix="/triage", tags=["artifacts"])


@router.get("/jobs/{job_id}/artifacts")
async def list_artifacts(job_id: int, db: DB, current_user: CurrentUser):
    """List artifact files for a job, grouped by node IP."""
    job = await _get_job(db, job_id)
    if not job.artifact_dir or not os.path.isdir(job.artifact_dir):
        return {"files": []}

    files = []
    for root, _dirs, filenames in os.walk(job.artifact_dir):
        for fname in filenames:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, job.artifact_dir)
            files.append({"path": rel, "size": os.path.getsize(fpath)})
    return {"files": files}


@router.get("/jobs/{job_id}/artifacts/download")
async def download_artifact(job_id: int, path: str, db: DB, current_user: CurrentUser):
    """Download a specific artifact file.  path is relative to the job's artifact_dir."""
    job = await _get_job(db, job_id)
    if not job.artifact_dir:
        raise HTTPException(status_code=404, detail="No artifacts for this job")

    # Security: ensure path stays within artifact_dir
    base = Path(job.artifact_dir).resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(target), filename=target.name)


async def _get_job(db, job_id: int) -> TriageJob:
    result = await db.execute(select(TriageJob).where(TriageJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
