from __future__ import annotations

import re
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ProcessRequest(BaseModel):
    url: str = Field(..., description="Video URL (YouTube, Vimeo, etc.)")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^https?://", v):
            raise ValueError("URL must start with http:// or https://")
        if len(v) > 2048:
            raise ValueError("URL exceeds maximum length")
        return v


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=50)
    backend: Literal["tfidf", "embeddings"] = "tfidf"


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class JobMetaResponse(BaseModel):
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    segment_count: Optional[int] = None
    chapter_count: Optional[int] = None
    highlight_count: Optional[int] = None
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    overall_status: str
    progress_pct: int
    ingest_status: str
    transcribe_status: str
    segment_status: str
    highlight_status: str
    summarise_status: str
    meta: JobMetaResponse
    error: Optional[str] = None
    error_stage: Optional[str] = None
    created_at: str
    updated_at: str

    @classmethod
    def from_job(cls, job) -> "JobResponse":
        return cls(
            job_id=job.job_id,
            overall_status=job.overall_status,
            progress_pct=job.progress_pct,
            ingest_status=job.ingest_status.value,
            transcribe_status=job.transcribe_status.value,
            segment_status=job.segment_status.value,
            highlight_status=job.highlight_status.value,
            summarise_status=job.summarise_status.value,
            meta=JobMetaResponse(**job.meta.model_dump()),
            error=job.error,
            error_stage=job.error_stage,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
        )


class SearchResult(BaseModel):
    text: str
    start: float
    end: float
    score: float
    backend: str


class SearchResponse(BaseModel):
    job_id: str
    query: str
    backend: str
    result_count: int
    results: list[SearchResult]


class ChapterItem(BaseModel):
    start: float
    end: float
    title: str
    segment_count: int


class ChaptersResponse(BaseModel):
    job_id: str
    chapters: list[ChapterItem]


class ClipItem(BaseModel):
    index: int
    filename: str
    url: str


class HighlightsResponse(BaseModel):
    job_id: str
    clip_count: int
    clips: list[ClipItem]


class ChapterSummary(BaseModel):
    title: str
    start: float
    end: float
    summary: str


class SummaryResponse(BaseModel):
    job_id: str
    overall: str
    chapters: list[ChapterSummary]


class HealthResponse(BaseModel):
    status: str
    version: str
    whisper_model: str
    search_backend: str
    summarise_backend: str
