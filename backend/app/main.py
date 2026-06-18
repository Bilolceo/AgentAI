"""FastAPI ilova kirish nuqtasi."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.app_env)
    yield
    log.info("shutdown")


app = FastAPI(title="AI Call-Center Agent", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
