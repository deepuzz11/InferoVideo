from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Literal
from backend.app.core.config import get_settings
from backend.app.models.schemas import (
    ChapterItem, ChaptersResponse, ChapterSummary,
    HealthResponse, HighlightsResponse, ClipItem,
    JobResponse, ProcessRequest, SearchRequest, SearchResponse, SearchResult,
    SummaryResponse, InsightsResponse, InsightItem,
)
from backend.app.services.pipeline import PipelineService

logger = logging.getLogger(__name__)
router = APIRouter()

_svc = PipelineService()
settings = get_settings()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return HealthResponse(
        status="ok",
        version=settings.version,
        whisper_model=settings.whisper_model,
        search_backend=settings.search_backend,
        summarise_backend=settings.summarise_backend,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

@router.post("/process", response_model=JobResponse, status_code=202, tags=["Pipeline"])
def process(body: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Start the full pipeline for a video URL (YouTube / Vimeo / etc.).
    Returns a job immediately — poll `GET /jobs/{job_id}` for progress.
    """
    job = _svc.create_job()
    background_tasks.add_task(_svc.run_pipeline, job.job_id, body.url)
    logger.info("Pipeline queued job=%s url=%s", job.job_id, body.url)
    return JobResponse.from_job(job)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.get("/jobs", tags=["Jobs"])
def list_jobs(limit: int = Query(20, ge=1, le=100)):
    jobs = _svc.list_jobs()[:limit]
    return {"jobs": [JobResponse.from_job(j) for j in jobs], "total": len(jobs)}


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(job_id: str):
    try:
        return JobResponse.from_job(_svc.get_job(job_id))
    except FileNotFoundError:
        raise HTTPException(404, f"Job '{job_id}' not found")


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.post("/jobs/{job_id}/search", response_model=SearchResponse, tags=["Search"])
def search(job_id: str, body: SearchRequest):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")

    if job.transcribe_status != "done":
        raise HTTPException(409, f"Transcription not complete (status: {job.transcribe_status})")

    raw = _svc.search(job_id, body.query, body.top_k, body.backend)
    return SearchResponse(
        job_id=job_id,
        query=body.query,
        backend=body.backend,
        result_count=len(raw),
        results=[SearchResult(**{k: r[k] for k in ("text","start","end","score","backend")}) for r in raw],
    )


# ---------------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/chapters", response_model=ChaptersResponse, tags=["Chapters"])
def get_chapters(job_id: str):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")

    if not job.chapter_path or not Path(job.chapter_path).exists():
        raise HTTPException(404, "Chapters not generated yet")

    raw = json.loads(Path(job.chapter_path).read_text())
    return ChaptersResponse(
        job_id=job_id,
        chapters=[ChapterItem(**ch) for ch in raw],
    )


# ---------------------------------------------------------------------------
# Highlights
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/highlights", response_model=HighlightsResponse, tags=["Highlights"])
def get_highlights(job_id: str):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")

    if job.highlight_status != "done":
        raise HTTPException(409, f"Highlights not ready (status: {job.highlight_status})")

    clips = sorted(Path(job.highlight_dir).glob("clip_*.mp4"))
    return HighlightsResponse(
        job_id=job_id,
        clip_count=len(clips),
        clips=[
            ClipItem(index=i + 1, filename=c.name, url=f"/data/highlights/{job_id}/{c.name}")
            for i, c in enumerate(clips)
        ],
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/summary", response_model=SummaryResponse, tags=["Summary"])
def get_summary(job_id: str):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")

    if job.summarise_status != "done":
        raise HTTPException(409, f"Summary not ready (status: {job.summarise_status})")

    from backend.app.core.summarise import load_summary
    data = load_summary(Path(job.summary_path))
    return SummaryResponse(
        job_id=job_id,
        overall=data["overall"],
        chapters=[ChapterSummary(**c) for c in data.get("chapters", [])],
    )


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/insights", response_model=InsightsResponse, tags=["Insights"])
def get_insights(job_id: str):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")

    if job.insights_status != "done":
        raise HTTPException(409, f"Insights not ready (status: {job.insights_status})")

    from backend.app.core.insights import load_insights
    data = load_insights(Path(job.insights_path))
    return InsightsResponse(
        job_id=job_id,
        entities=[InsightItem(**e) for e in data.get("entities", [])],
        keywords=[InsightItem(**k) for k in data.get("keywords", [])],
    )


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/export/{fmt}", tags=["Exports"])
def export_subtitles(job_id: str, fmt: Literal["srt", "vtt"]):
    try:
        content = _svc.get_subtitles(job_id, fmt)
        filename = f"subtitles_{job_id}.{fmt}"
        from fastapi.responses import Response
        media_type = "text/vtt" if fmt == "vtt" else "text/plain"
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as exc:
        raise HTTPException(400, str(exc))


# ---------------------------------------------------------------------------
# Per-stage re-trigger (dev / debugging)
# ---------------------------------------------------------------------------

@router.post("/jobs/{job_id}/retranscribe", tags=["Pipeline"])
def retranscribe(job_id: str, background_tasks: BackgroundTasks):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")
    if not job.video_path:
        raise HTTPException(409, "No video on this job")
    background_tasks.add_task(_svc.run_transcribe, job)
    return {"status": "queued", "stage": "transcribe", "job_id": job_id}


@router.post("/jobs/{job_id}/resegment", tags=["Pipeline"])
def resegment(job_id: str, background_tasks: BackgroundTasks):
    try:
        job = _svc.get_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job not found")
    if not job.transcript_path:
        raise HTTPException(409, "No transcript on this job")
    background_tasks.add_task(_svc.run_segment, job)
    return {"status": "queued", "stage": "segment", "job_id": job_id}
