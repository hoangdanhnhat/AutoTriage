import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.models import User, Inventory, Node, NodeStatus, TriageJob, NodeTriageStatus  # registers all models
from app.routers import auth, inventories, nodes, triage, artifacts
from app.websocket.manager import manager
from app.utils.auth import decode_token, hash_password

from fastapi.responses import RedirectResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Digital Triage Forensics", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(inventories.router)
app.include_router(nodes.router)
app.include_router(triage.router)
app.include_router(artifacts.router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# ── WebSocket ──────────────────────────────────────────────────────────────────
@app.websocket("/ws/triage/{job_id}")
async def triage_ws(websocket: WebSocket, job_id: int, token: str | None = None):
    """
    WebSocket endpoint. Pass JWT via ?token=<token> query parameter.
    """
    if not token:
        await websocket.close(code=4001)
        return
    username = decode_token(token)
    if not username:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive; we only push from server
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


# ── Startup: create tables + seed admin user ───────────────────────────────────
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.admin_username))
        existing = result.scalar_one_or_none()
        if existing is None:
            admin = User(
                username=settings.admin_username,
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            await db.commit()
            logger.info("Seeded admin user: %s", settings.admin_username)
