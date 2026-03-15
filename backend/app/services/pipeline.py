from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.core.highlight import cut_clips, merge_adjacent, score_segments, select_highlights
from backend.app.core.ingest import IngestError, ingest_video
from backend.app.core.search import search_segments
from backend.app.core.segment import save_chapters, segment_chapters
from backend.app.core.summarise import (
    load_summary, save_summary, summarise_chapters, summarise_transcript,
)
from backend.app.core.transcribe import TranscribeError, load_transcript, save_transcript, transcribe_video
from backend.app.models.video_job import PipelineStage, StageStatus, VideoJob

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self):
        self.settings = get_settings()
        self._executor = ThreadPoolExecutor(max_workers=4)

    # ------------------------------------------------------------------ #
    # Job management
    # ------------------------------------------------------------------ #

    def create_job(self) -> VideoJob:
        job = VideoJob()
        job.save(self.settings.jobs_dir)
        return job

    def get_job(self, job_id: str) -> VideoJob:
        return VideoJob.load(job_id, self.settings.jobs_dir)

    def list_jobs(self) -> list[VideoJob]:
        return VideoJob.list_all(self.settings.jobs_dir)

    def _save(self, job: VideoJob):
        job.save(self.settings.jobs_dir)

    # ------------------------------------------------------------------ #
    # Stages
    # ------------------------------------------------------------------ #

    def run_ingest(self, job: VideoJob, url: str):
        job.set_stage(PipelineStage.INGEST, StageStatus.RUNNING)
        job.meta.source_url = url
        self._save(job)
        try:
            result = ingest_video(url, self.settings.video_dir)
            job.video_path = result["video_path"]
            job.meta.title = result.get("title", job.job_id)
            job.meta.thumbnail_url = result.get("thumbnail_url", "")
            if result.get("duration"):
                job.meta.duration_seconds = float(result["duration"])
            job.set_stage(PipelineStage.INGEST, StageStatus.DONE)
        except IngestError as exc:
            job.set_stage(PipelineStage.INGEST, StageStatus.FAILED, str(exc))
            raise
        finally:
            self._save(job)

    def run_transcribe(self, job: VideoJob):
        job.set_stage(PipelineStage.TRANSCRIBE, StageStatus.RUNNING)
        self._save(job)
        try:
            segments = transcribe_video(Path(job.video_path), self.settings.whisper_model)
            path = save_transcript(job.job_id, segments, self.settings.transcript_dir)
            job.transcript_path = str(path)
            job.meta.segment_count = len(segments)
            if segments:
                job.meta.duration_seconds = job.meta.duration_seconds or segments[-1]["end"]
            job.set_stage(PipelineStage.TRANSCRIBE, StageStatus.DONE)
        except TranscribeError as exc:
            job.set_stage(PipelineStage.TRANSCRIBE, StageStatus.FAILED, str(exc))
            raise
        finally:
            self._save(job)

    def run_segment(self, job: VideoJob):
        job.set_stage(PipelineStage.SEGMENT, StageStatus.RUNNING)
        self._save(job)
        try:
            segments = load_transcript(Path(job.transcript_path))
            chapters = segment_chapters(
                segments,
                window_size=self.settings.chapter_window_size,
                threshold=self.settings.chapter_threshold,
            )
            path = save_chapters(job.job_id, chapters, self.settings.chapter_dir)
            job.chapter_path = str(path)
            job.meta.chapter_count = len(chapters)
            job.set_stage(PipelineStage.SEGMENT, StageStatus.DONE)
        except Exception as exc:
            job.set_stage(PipelineStage.SEGMENT, StageStatus.FAILED, str(exc))
            raise
        finally:
            self._save(job)

    def run_highlight(self, job: VideoJob):
        job.set_stage(PipelineStage.HIGHLIGHT, StageStatus.RUNNING)
        self._save(job)
        try:
            segments = load_transcript(Path(job.transcript_path))
            scores = score_segments(segments)
            raw = select_highlights(segments, scores, self.settings.highlight_threshold)
            merged = merge_adjacent(raw, self.settings.merge_gap_seconds)
            out_dir = self.settings.highlight_dir / job.job_id
            clips = cut_clips(Path(job.video_path), merged, out_dir, self.settings.max_clip_duration)
            job.highlight_dir = str(out_dir)
            job.meta.highlight_count = len(clips)
            job.set_stage(PipelineStage.HIGHLIGHT, StageStatus.DONE)
        except Exception as exc:
            job.set_stage(PipelineStage.HIGHLIGHT, StageStatus.FAILED, str(exc))
            raise
        finally:
            self._save(job)

    def run_summarise(self, job: VideoJob):
        job.set_stage(PipelineStage.SUMMARISE, StageStatus.RUNNING)
        self._save(job)
        try:
            segments = load_transcript(Path(job.transcript_path))
            chapters = []
            if job.chapter_path and Path(job.chapter_path).exists():
                import json
                chapters = json.loads(Path(job.chapter_path).read_text())

            overall = summarise_transcript(
                segments,
                backend=self.settings.summarise_backend,
                model_name=self.settings.summarise_model,
                max_length=self.settings.summary_max_length,
                min_length=self.settings.summary_min_length,
            )

            chapter_summaries = summarise_chapters(
                segments, chapters,
                backend=self.settings.summarise_backend,
                model_name=self.settings.summarise_model,
            ) if chapters else []

            payload = {
                "job_id": job.job_id,
                "overall": overall,
                "chapters": chapter_summaries,
            }
            path = save_summary(job.job_id, payload, self.settings.summary_dir)
            job.summary_path = str(path)
            job.set_stage(PipelineStage.SUMMARISE, StageStatus.DONE)
        except Exception as exc:
            job.set_stage(PipelineStage.SUMMARISE, StageStatus.FAILED, str(exc))
            raise
        finally:
            self._save(job)

    # ------------------------------------------------------------------ #
    # Full pipeline
    # ------------------------------------------------------------------ #

    async def run_pipeline(self, job_id: str, url: str):
        """Full pipeline: ingest → transcribe → segment → highlight → summarise."""
        job = self.get_job(job_id)
        loop = asyncio.get_running_loop()

        try:
            # Stage 1: Ingest (Sequential)
            await loop.run_in_executor(self._executor, self.run_ingest, job, url)

            # Stage 2: Transcribe (Sequential, bottleneck for following stages)
            await loop.run_in_executor(self._executor, self.run_transcribe, job)

            # Stage 3: Parallel processing (Segment, Highlight)
            # Summarise usually depends on segments for chapter summaries,
            # so we run it after segments but parallel with highlights.

            async def run_stage_in_executor(stage_func, *args):
                return await loop.run_in_executor(self._executor, stage_func, *args)

            # Run segment and highlight in parallel
            segment_task = asyncio.create_task(run_stage_in_executor(self.run_segment, job))
            highlight_task = asyncio.create_task(run_stage_in_executor(self.run_highlight, job))

            await segment_task  # Wait for segment to finish before starting summary
            summary_task = asyncio.create_task(run_stage_in_executor(self.run_summarise, job))

            await asyncio.gather(highlight_task, summary_task)

            logger.info("Pipeline complete: %s", job_id)
        except Exception as exc:
            logger.error("Pipeline failed for %s: %s", job_id, exc)

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #

    def search(self, job_id: str, query: str, top_k: int = 5, backend: str = "tfidf") -> list[dict]:
        job = self.get_job(job_id)
        if not job.transcript_path:
            raise ValueError("No transcript available for this job")
        segments = load_transcript(Path(job.transcript_path))
        return search_segments(
            segments, query, top_k=top_k,
            backend=backend, embedding_model=self.settings.embedding_model,
        )
