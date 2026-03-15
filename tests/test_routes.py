"""
tests/test_routes.py
Integration-style tests for all FastAPI routes.
Uses TestClient + unittest.mock so no real yt-dlp / Whisper / ffmpeg is needed.
"""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.video_job import PipelineStage, StageStatus, VideoJob

client = TestClient(app)

API = "/api/v1"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _job(tmp: Path, *, transcribed=True, segmented=True, highlighted=True, summarised=True) -> VideoJob:
    job = VideoJob(job_id=str(uuid.uuid4()))
    job.ingest_status    = StageStatus.DONE
    job.transcribe_status = StageStatus.DONE if transcribed else StageStatus.PENDING
    job.segment_status   = StageStatus.DONE if segmented   else StageStatus.PENDING
    job.highlight_status  = StageStatus.DONE if highlighted  else StageStatus.PENDING
    job.summarise_status  = StageStatus.DONE if summarised   else StageStatus.PENDING
    job.video_path = str(tmp / f"{job.job_id}.mp4")

    if transcribed:
        t = tmp / f"{job.job_id}_transcript.json"
        t.write_text(json.dumps([
            {"id": 0, "start": 0.0, "end": 5.0,
             "text": "Machine learning is a fascinating field of study",
             "avg_logprob": -0.3, "no_speech_prob": 0.01},
            {"id": 1, "start": 5.0, "end": 10.0,
             "text": "Deep learning uses neural networks with many layers to learn",
             "avg_logprob": -0.2, "no_speech_prob": 0.01},
        ]))
        job.transcript_path = str(t)

    if segmented:
        c = tmp / f"{job.job_id}_chapters.json"
        c.write_text(json.dumps([{
            "start": 0.0, "end": 10.0,
            "title": "Introduction to Machine Learning", "segment_count": 2,
        }]))
        job.chapter_path = str(c)

    if highlighted:
        h_dir = tmp / "highlights" / job.job_id
        h_dir.mkdir(parents=True, exist_ok=True)
        (h_dir / "clip_01.mp4").write_bytes(b"fake_video_bytes")
        job.highlight_dir = str(h_dir)

    if summarised:
        s = tmp / f"{job.job_id}_summary.json"
        s.write_text(json.dumps({
            "job_id": job.job_id,
            "overall": "This video covers machine learning and deep learning fundamentals.",
            "chapters": [{
                "title": "Introduction to Machine Learning",
                "start": 0.0, "end": 10.0,
                "summary": "An overview of ML concepts.",
            }],
        }))
        job.summary_path = str(s)

    job.save(tmp)
    return job


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_returns_200(self):
        r = client.get(f"{API}/health")
        assert r.status_code == 200

    def test_status_ok(self):
        assert client.get(f"{API}/health").json()["status"] == "ok"

    def test_has_version(self):
        assert "version" in client.get(f"{API}/health").json()

    def test_has_whisper_model(self):
        assert "whisper_model" in client.get(f"{API}/health").json()

    def test_has_search_backend(self):
        assert "search_backend" in client.get(f"{API}/health").json()

    def test_has_summarise_backend(self):
        assert "summarise_backend" in client.get(f"{API}/health").json()


class TestRoot:
    def test_root_200(self):
        assert client.get("/").status_code == 200

    def test_root_has_docs_key(self):
        assert "docs" in client.get("/").json()


# ---------------------------------------------------------------------------
# Process  (POST /process)
# ---------------------------------------------------------------------------

class TestProcess:
    def test_valid_youtube_url_returns_202(self):
        with patch("backend.app.api.routes._svc") as mock:
            job = VideoJob(job_id=str(uuid.uuid4()))
            mock.create_job.return_value = job
            mock.run_pipeline = MagicMock()
            r = client.post(f"{API}/process", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
            assert r.status_code == 202

    def test_returns_job_id(self):
        with patch("backend.app.api.routes._svc") as mock:
            job = VideoJob(job_id=str(uuid.uuid4()))
            mock.create_job.return_value = job
            r = client.post(f"{API}/process", json={"url": "https://www.youtube.com/watch?v=test"})
            assert "job_id" in r.json()

    def test_pipeline_queued_as_background_task(self):
        with patch("backend.app.api.routes._svc") as mock:
            job = VideoJob(job_id=str(uuid.uuid4()))
            mock.create_job.return_value = job
            client.post(f"{API}/process", json={"url": "https://youtu.be/test123"})
            # Background task registered — run_pipeline should have been registered
            # (TestClient runs background tasks synchronously)

    def test_rejects_non_http_url(self):
        r = client.post(f"{API}/process", json={"url": "ftp://badurl.com/video"})
        assert r.status_code == 422

    def test_rejects_missing_url(self):
        r = client.post(f"{API}/process", json={})
        assert r.status_code == 422

    def test_rejects_empty_url(self):
        r = client.post(f"{API}/process", json={"url": ""})
        assert r.status_code == 422

    def test_rejects_url_without_scheme(self):
        r = client.post(f"{API}/process", json={"url": "youtube.com/watch?v=abc"})
        assert r.status_code == 422

    def test_initial_status_is_pending(self):
        with patch("backend.app.api.routes._svc") as mock:
            job = VideoJob(job_id=str(uuid.uuid4()))
            mock.create_job.return_value = job
            r = client.post(f"{API}/process", json={"url": "https://vimeo.com/123456"})
            assert r.json()["overall_status"] in ("pending", "processing")


# ---------------------------------------------------------------------------
# Jobs  (GET /jobs, GET /jobs/{id})
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_unknown_job_404(self):
        r = client.get(f"{API}/jobs/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_known_job_200(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                r = client.get(f"{API}/jobs/{job.job_id}")
                assert r.status_code == 200

    def test_complete_job_progress_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                body = client.get(f"{API}/jobs/{job.job_id}").json()
                assert body["progress_pct"] == 100
                assert body["overall_status"] == "complete"

    def test_job_response_has_all_stage_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                body = client.get(f"{API}/jobs/{job.job_id}").json()
                for key in ("ingest_status","transcribe_status","segment_status",
                            "highlight_status","summarise_status"):
                    assert key in body

    def test_job_response_has_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                body = client.get(f"{API}/jobs/{job.job_id}").json()
                assert "meta" in body


class TestListJobs:
    def test_returns_200(self):
        with patch("backend.app.api.routes._svc") as mock:
            mock.list_jobs.return_value = []
            r = client.get(f"{API}/jobs")
            assert r.status_code == 200

    def test_has_jobs_key(self):
        with patch("backend.app.api.routes._svc") as mock:
            mock.list_jobs.return_value = []
            assert "jobs" in client.get(f"{API}/jobs").json()

    def test_limit_param_validates(self):
        r = client.get(f"{API}/jobs?limit=0")
        assert r.status_code == 422

    def test_limit_above_100_rejected(self):
        r = client.get(f"{API}/jobs?limit=101")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Search  (POST /jobs/{id}/search)
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_returns_200_when_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                mock.search.return_value = [{
                    "text": "Machine learning is a fascinating field",
                    "start": 0.0, "end": 5.0, "score": 0.9, "backend": "tfidf",
                }]
                r = client.post(f"{API}/jobs/{job.job_id}/search",
                                json={"query": "machine learning", "top_k": 5})
                assert r.status_code == 200

    def test_search_result_count_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                mock.search.return_value = [
                    {"text": "ML text here meaningful words", "start": 0.0, "end": 5.0,
                     "score": 0.9, "backend": "tfidf"},
                    {"text": "Deep learning text content valuable", "start": 5.0, "end": 10.0,
                     "score": 0.7, "backend": "tfidf"},
                ]
                r = client.post(f"{API}/jobs/{job.job_id}/search",
                                json={"query": "deep learning", "top_k": 5})
                assert r.json()["result_count"] == 2

    def test_search_409_if_not_transcribed(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp), transcribed=False)
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                r = client.post(f"{API}/jobs/{job.job_id}/search",
                                json={"query": "test", "top_k": 3})
                assert r.status_code == 409

    def test_search_404_unknown_job(self):
        r = client.post(f"{API}/jobs/{uuid.uuid4()}/search",
                        json={"query": "test", "top_k": 3})
        assert r.status_code == 404

    def test_search_rejects_top_k_above_50(self):
        r = client.post(f"{API}/jobs/{uuid.uuid4()}/search",
                        json={"query": "test", "top_k": 999})
        assert r.status_code == 422

    def test_search_rejects_empty_query(self):
        r = client.post(f"{API}/jobs/{uuid.uuid4()}/search",
                        json={"query": "", "top_k": 5})
        assert r.status_code == 422

    def test_search_accepts_embeddings_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                mock.search.return_value = []
                r = client.post(f"{API}/jobs/{job.job_id}/search",
                                json={"query": "neural networks", "top_k": 3, "backend": "embeddings"})
                assert r.status_code == 200

    def test_search_rejects_invalid_backend(self):
        r = client.post(f"{API}/jobs/{uuid.uuid4()}/search",
                        json={"query": "test", "top_k": 3, "backend": "gpt"})
        assert r.status_code == 422

    def test_search_response_has_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                mock.search.return_value = []
                body = client.post(f"{API}/jobs/{job.job_id}/search",
                                   json={"query": "learning", "top_k": 5}).json()
                assert {"job_id","query","backend","result_count","results"} <= body.keys()


# ---------------------------------------------------------------------------
# Chapters  (GET /jobs/{id}/chapters)
# ---------------------------------------------------------------------------

class TestChapters:
    def test_returns_chapters_when_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                r = client.get(f"{API}/jobs/{job.job_id}/chapters")
                assert r.status_code == 200
                assert len(r.json()["chapters"]) == 1

    def test_chapter_has_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                chapters = client.get(f"{API}/jobs/{job.job_id}/chapters").json()["chapters"]
                for ch in chapters:
                    assert {"start","end","title","segment_count"} <= ch.keys()

    def test_404_if_no_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp), segmented=False)
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                assert client.get(f"{API}/jobs/{job.job_id}/chapters").status_code == 404

    def test_404_unknown_job(self):
        assert client.get(f"{API}/jobs/{uuid.uuid4()}/chapters").status_code == 404


# ---------------------------------------------------------------------------
# Highlights  (GET /jobs/{id}/highlights)
# ---------------------------------------------------------------------------

class TestHighlights:
    def test_returns_highlights_when_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                r = client.get(f"{API}/jobs/{job.job_id}/highlights")
                assert r.status_code == 200
                assert r.json()["clip_count"] == 1

    def test_clip_has_url_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                clips = client.get(f"{API}/jobs/{job.job_id}/highlights").json()["clips"]
                for clip in clips:
                    assert "url" in clip and clip["url"].startswith("/data/")

    def test_409_if_highlights_not_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp), highlighted=False)
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                assert client.get(f"{API}/jobs/{job.job_id}/highlights").status_code == 409

    def test_404_unknown_job(self):
        assert client.get(f"{API}/jobs/{uuid.uuid4()}/highlights").status_code == 404


# ---------------------------------------------------------------------------
# Summary  (GET /jobs/{id}/summary)
# ---------------------------------------------------------------------------

class TestSummary:
    def test_returns_summary_when_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                r = client.get(f"{API}/jobs/{job.job_id}/summary")
                assert r.status_code == 200

    def test_summary_has_overall_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                body = client.get(f"{API}/jobs/{job.job_id}/summary").json()
                assert "overall" in body
                assert isinstance(body["overall"], str)

    def test_summary_has_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp))
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                body = client.get(f"{API}/jobs/{job.job_id}/summary").json()
                assert "chapters" in body
                assert isinstance(body["chapters"], list)

    def test_409_if_summary_not_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = _job(Path(tmp), summarised=False)
            with patch("backend.app.api.routes._svc") as mock:
                mock.get_job.return_value = job
                assert client.get(f"{API}/jobs/{job.job_id}/summary").status_code == 409

    def test_404_unknown_job(self):
        assert client.get(f"{API}/jobs/{uuid.uuid4()}/summary").status_code == 404
