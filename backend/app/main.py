from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.core.config import get_settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "root": {"level": "INFO", "handlers": ["console"]},
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    s.ensure_dirs()
    logger.info("InferaVideo %s ready | whisper=%s search=%s summarise=%s",
                s.version, s.whisper_model, s.search_backend, s.summarise_backend)
    yield
    logger.info("InferaVideo shutting down")


settings = get_settings()

app = FastAPI(
    title="InferaVideo API",
    description=(
        "Local-first video intelligence: transcribe, search, chapter-segment, "
        "highlight-extract, and summarise any video — no cloud APIs required."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory=str(settings.data_dir)), name="data")
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["System"])
def root():
    return {"service": "InferaVideo", "version": settings.version, "docs": "/docs"}
