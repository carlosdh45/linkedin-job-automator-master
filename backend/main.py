import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import db as src_db
from backend.api import (
    application_packet,
    auth,
    cv_import,
    daily_brief,
    demo,
    health,
    jobs,
    leads,
    profile,
    resume,
    review,
    stats,
    bd_companies,
    bd_prospects,
    bd_signals,
    bd_opportunities,
    bd_deal_packets,
    bd_pipeline,
    bd_demo,
    bd_message_studio,
    bd_outreach_drafts,
    bd_activity,
    bd_icp,
    bd_dashboard,
    bd_recommendations,
    bd_import,
    bd_workspace,
    bd_export,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.environ.get("DOBRYBOT_DB_PATH", "data/copilot.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    src_db.initialize_database(db_path)
    logger.info(f"DobryBot API started. DB: {db_path}")
    yield
    logger.info("DobryBot API shutdown.")


app = FastAPI(
    title="DobryBot API",
    description="Human-in-the-loop opportunity and growth assistant — never sends or applies automatically.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stats.router, prefix="/api")
app.include_router(daily_brief.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(cv_import.router, prefix="/api")
app.include_router(application_packet.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# BD OS routers
app.include_router(bd_companies.router, prefix="/api")
app.include_router(bd_prospects.router, prefix="/api")
app.include_router(bd_signals.router, prefix="/api")
app.include_router(bd_opportunities.router, prefix="/api")
app.include_router(bd_deal_packets.router, prefix="/api")
app.include_router(bd_pipeline.router, prefix="/api")
app.include_router(bd_demo.router, prefix="/api")
app.include_router(bd_message_studio.router, prefix="/api")
app.include_router(bd_outreach_drafts.router, prefix="/api")
app.include_router(bd_activity.router, prefix="/api")
app.include_router(bd_icp.router, prefix="/api")
app.include_router(bd_dashboard.router, prefix="/api")
app.include_router(bd_recommendations.router, prefix="/api")
app.include_router(bd_import.router, prefix="/api")
app.include_router(bd_workspace.router, prefix="/api")
app.include_router(bd_export.router, prefix="/api")
