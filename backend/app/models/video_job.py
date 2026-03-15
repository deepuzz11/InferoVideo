from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStage(str, Enum):
    INGEST = "ingest"
    TRANSCRIBE = "transcribe"
    SEGMENT = "segment"
    HIGHLIGHT = "highlight"
    SUMMARISE = "summarise"


class JobMeta(BaseModel):
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    segment_count: Optional[int] = None
    chapter_count: Optional[int] = None
    highlight_count: Optional[int] = None
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class VideoJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))

    # Stage statuses
    ingest_status: StageStatus = StageStatus.PENDING
    transcribe_status: StageStatus = StageStatus.PENDING
    segment_status: StageStatus = StageStatus.PENDING
    highlight_status: StageStatus = StageStatus.PENDING
    summarise_status: StageStatus = StageStatus.PENDING

    # Artifact paths
    video_path: Optional[str] = None
    transcript_path: Optional[str] = None
    chapter_path: Optional[str] = None
    highlight_dir: Optional[str] = None
    summary_path: Optional[str] = None

    # Rich metadata
    meta: JobMeta = Field(default_factory=JobMeta)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    error_stage: Optional[str] = None

    def set_stage(self, stage: PipelineStage, status: StageStatus, error: str | None = None):
        setattr(self, f"{stage.value}_status", status)
        self.updated_at = datetime.now(timezone.utc)
        if error:
            self.error = error
            self.error_stage = stage.value

    @property
    def overall_status(self) -> str:
        statuses = [
            self.ingest_status, self.transcribe_status,
            self.segment_status, self.highlight_status, self.summarise_status,
        ]
        if any(s == StageStatus.FAILED for s in statuses):
            return "failed"
        if all(s in (StageStatus.DONE, StageStatus.SKIPPED) for s in statuses):
            return "complete"
        if any(s == StageStatus.RUNNING for s in statuses):
            return "processing"
        return "pending"

    @property
    def progress_pct(self) -> int:
        weights = {StageStatus.DONE: 1, StageStatus.RUNNING: 0.5, StageStatus.SKIPPED: 1}
        stages = [
            self.ingest_status, self.transcribe_status,
            self.segment_status, self.highlight_status, self.summarise_status,
        ]
        earned = sum(weights.get(s, 0) for s in stages)
        return int((earned / len(stages)) * 100)

    def save(self, jobs_dir: Path):
        jobs_dir.mkdir(parents=True, exist_ok=True)
        path = jobs_dir / f"{self.job_id}.json"
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, job_id: str, jobs_dir: Path) -> "VideoJob":
        path = jobs_dir / f"{job_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Job {job_id} not found")
        return cls.model_validate_json(path.read_text())

    @classmethod
    def list_all(cls, jobs_dir: Path) -> list["VideoJob"]:
        jobs = []
        for p in sorted(jobs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                jobs.append(cls.model_validate_json(p.read_text()))
            except Exception:
                pass
        return jobs
