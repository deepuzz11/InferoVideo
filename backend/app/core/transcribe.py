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
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscribeError("faster-whisper is not installed. Run: pip install faster-whisper") from exc
    logger.info("Loading FasterWhisper '%s' model …", model_name)
    # Using float16 for speed on GPU, or int8 for CPU efficiency
    # In a local environment, we'll auto-detect
    return WhisperModel(model_name, device="auto", compute_type="default")


def transcribe_video(video_path: Path, model_name: str = "base") -> list[dict[str, Any]]:
    if not video_path.exists():
        raise TranscribeError(f"Video not found: {video_path}")

    model = _load_model(model_name)
    logger.info("Transcribing %s …", video_path.name)

    segments_gen, info = model.transcribe(
        str(video_path),
        beam_size=5,
        word_timestamps=False,
        condition_on_previous_text=True,
    )

    segments = []
    for i, seg in enumerate(segments_gen):
        segments.append({
            "id": i,
            "start": round(float(seg.start), 3),
            "end": round(float(seg.end), 3),
            "text": seg.text.strip(),
            "avg_logprob": round(float(seg.avg_logprob), 4),
            "no_speech_prob": round(float(seg.no_speech_prob), 4),
        })

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
