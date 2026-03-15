from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class IngestError(Exception):
    pass


def ingest_video(url: str, video_dir: Path) -> dict:
    """
    Download a video from *url* using yt-dlp.
    Cross-platform (Windows / macOS / Linux).

    Strategy:
      - Snapshot existing files before download
      - Let yt-dlp write whatever filename it likes
      - After download, detect the new file by diffing the directory
      - Rename it to <job_id>.mp4
    """
    job_id = str(uuid.uuid4())
    video_dir.mkdir(parents=True, exist_ok=True)

    # Fetch metadata first (best-effort)
    meta = _fetch_metadata(url)

    # ── Snapshot files already in video_dir ──────────────────────────────
    before: set[Path] = set(video_dir.iterdir())

    # Use a dedicated temp subdir so we only pick up THIS download
    tmp_dir = video_dir / f"_tmp_{job_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--no-progress",
        "-o", str(tmp_dir / "video.%(ext)s"),
        url,
    ]

    logger.info("Ingesting %s", url)
    logger.debug("cmd: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        logger.debug("yt-dlp stdout: %s", result.stdout[-400:])
    except subprocess.CalledProcessError as exc:
        _cleanup(tmp_dir)
        stderr = (exc.stderr or "")[-800:]
        raise IngestError(f"yt-dlp failed: {stderr}") from exc
    except subprocess.TimeoutExpired as exc:
        _cleanup(tmp_dir)
        raise IngestError("Download timed out after 10 minutes") from exc
    except FileNotFoundError:
        raise IngestError(
            "yt-dlp not found. Install it: pip install yt-dlp"
        )

    # ── Find what yt-dlp wrote inside tmp_dir ────────────────────────────
    candidates = [
        p for p in tmp_dir.iterdir()
        if p.is_file() and p.suffix.lower() not in (".part", ".ytdl", ".tmp")
    ]

    if not candidates:
        _cleanup(tmp_dir)
        raise IngestError(
            f"yt-dlp exited successfully but no file found in {tmp_dir}. "
            f"stdout: {result.stdout[-400:]}"
        )

    # Pick the largest file (in case of stray thumbnails etc.)
    downloaded = max(candidates, key=lambda p: p.stat().st_size)
    logger.info("yt-dlp produced: %s (%.1f MB)",
                downloaded.name, downloaded.stat().st_size / 1_048_576)

    # ── Move / remux into final location ─────────────────────────────────
    final_path = video_dir / f"{job_id}.mp4"

    if downloaded.suffix.lower() == ".mp4":
        shutil.move(str(downloaded), str(final_path))
    else:
        logger.info("Re-muxing %s → mp4 (stream copy)", downloaded.suffix)
        _remux(downloaded, final_path)
        try:
            downloaded.unlink()
        except OSError:
            pass

    _cleanup(tmp_dir)

    if not final_path.exists():
        raise IngestError(f"Post-processing failed — {final_path} not found")

    logger.info("Ingest complete → %s (%.1f MB)",
                final_path, final_path.stat().st_size / 1_048_576)

    return {
        "job_id": job_id,
        "video_path": str(final_path),
        "title": meta.get("title", job_id),
        "thumbnail_url": meta.get("thumbnail", ""),
        "duration": meta.get("duration", 0),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _remux(src: Path, dst: Path):
    """Stream-copy src into mp4 container via ffmpeg (no re-encode)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-c", "copy",
        "-movflags", "+faststart",
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.warning("ffmpeg remux failed (%s); copying as-is", exc)
        shutil.copy2(str(src), str(dst))


def _cleanup(path: Path):
    """Remove a temp directory, ignoring errors."""
    try:
        shutil.rmtree(str(path), ignore_errors=True)
    except Exception:
        pass


def _fetch_metadata(url: str) -> dict:
    """Use yt-dlp --dump-json to retrieve video metadata without downloading."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip().splitlines()[0])
    except Exception as exc:
        logger.warning("Metadata fetch failed (non-fatal): %s", exc)
    return {}