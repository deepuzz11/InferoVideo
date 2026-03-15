from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TranscribeError(Exception):
    pass


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    try:
        import whisper
    except ImportError as exc:
        raise TranscribeError("openai-whisper is not installed. Run: pip install openai-whisper") from exc
    logger.info("Loading Whisper '%s' model …", model_name)
    return whisper.load_model(model_name)


def transcribe_video(video_path: Path, model_name: str = "base") -> list[dict[str, Any]]:
    if not video_path.exists():
        raise TranscribeError(f"Video not found: {video_path}")

    model = _load_model(model_name)
    logger.info("Transcribing %s …", video_path.name)

    result = model.transcribe(
        str(video_path),
        verbose=False,
        word_timestamps=False,
        condition_on_previous_text=True,
    )

    segments = [
        {
            "id": int(seg["id"]),
            "start": round(float(seg["start"]), 3),
            "end": round(float(seg["end"]), 3),
            "text": seg["text"].strip(),
            "avg_logprob": round(float(seg.get("avg_logprob", 0.0)), 4),
            "no_speech_prob": round(float(seg.get("no_speech_prob", 0.0)), 4),
        }
        for seg in result["segments"]
    ]

    logger.info("Transcription done: %d segments", len(segments))
    return segments


def save_transcript(job_id: str, segments: list[dict], transcript_dir: Path) -> Path:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    out = transcript_dir / f"{job_id}.json"
    out.write_text(json.dumps(segments, indent=2, ensure_ascii=False))
    return out


def load_transcript(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {path}")
    return json.loads(path.read_text())
