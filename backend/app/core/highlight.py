from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class HighlightError(Exception):
    pass


def score_segments(segments: list[dict[str, Any]]) -> np.ndarray:
    texts = [s["text"] for s in segments]
    try:
        vec = TfidfVectorizer(stop_words="english")
        X = vec.fit_transform(texts)
        tfidf = np.asarray(X.sum(axis=1)).flatten()
    except ValueError:
        tfidf = np.ones(len(texts))

    lengths = np.array([len(t.split()) for t in texts], dtype=float)
    confidence = np.array([1.0 - s.get("no_speech_prob", 0.0) for s in segments])

    def _norm(arr):
        return arr / (arr.max() + 1e-9)

    return 0.6 * _norm(tfidf) + 0.2 * _norm(lengths) + 0.2 * confidence


def select_highlights(
    segments: list[dict[str, Any]],
    scores: np.ndarray,
    threshold: float = 0.75,
) -> list[dict[str, Any]]:
    return [
        {"start": seg["start"], "end": seg["end"], "score": round(float(sc), 4), "text": seg["text"]}
        for seg, sc in zip(segments, scores)
        if sc >= threshold
    ]


def merge_adjacent(highlights: list[dict[str, Any]], gap: float = 3.0) -> list[dict[str, Any]]:
    if not highlights:
        return []
    merged = [dict(highlights[0])]
    for h in highlights[1:]:
        last = merged[-1]
        if h["start"] - last["end"] <= gap:
            last["end"] = h["end"]
            last["score"] = max(last["score"], h["score"])
            last["text"] = last["text"] + " " + h["text"]
        else:
            merged.append(dict(h))
    return merged


def cut_clips(
    video_path: Path,
    clips: list[dict[str, Any]],
    out_dir: Path,
    max_len: int = 60,
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for i, clip in enumerate(clips, start=1):
        start = clip["start"]
        duration = min(max_len, clip["end"] - start)
        out = out_dir / f"clip_{i:02d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out),
        ]

        logger.info("Cutting clip %d (%.1fs–%.1fs)", i, start, start + duration)
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        except subprocess.CalledProcessError as exc:
            logger.error("ffmpeg error clip %d: %s", i, exc.stderr.decode()[-400:])
            continue

        outputs.append({
            "clip_path": str(out),
            "start": start,
            "end": round(start + duration, 2),
            "score": clip["score"],
            "index": i,
        })

    return outputs
