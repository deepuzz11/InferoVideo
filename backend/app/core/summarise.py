"""
summarise.py
============
Two-backend summarisation pipeline:

* extractive  – fast, zero-dependency TextRank-style sentence scoring
                (uses only sklearn + numpy, always available)
* transformers – HuggingFace abstractive summarisation
                 (requires ``transformers`` + ``torch``; falls back to
                  extractive if unavailable)

Public entry-points
-------------------
summarise_transcript(segments, ...)  → full-video summary string
summarise_chapters(segments, chapters, ...) → per-chapter summary list
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extractive summariser (TextRank-lite)
# ---------------------------------------------------------------------------

def _sentence_scores(sentences: list[str]) -> np.ndarray:
    """Score sentences by mean TF-IDF similarity to the corpus centroid."""
    if len(sentences) < 2:
        return np.ones(len(sentences))
    try:
        vec = TfidfVectorizer(stop_words="english")
        X = vec.fit_transform(sentences)
        centroid = X.mean(axis=0)
        scores = cosine_similarity(X, centroid).flatten()
        return scores
    except Exception:
        return np.ones(len(sentences))


def _extractive_summary(text: str, max_sentences: int = 5) -> str:
    """Return a multi-sentence extractive summary of *text*."""
    # Split on sentence boundaries
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in raw if len(s.split()) >= 5]
    if not sentences:
        return text[:500]

    scores = _sentence_scores(sentences)
    n = min(max_sentences, len(sentences))
    # Pick top-n by score, re-order by original position
    top_idx = sorted(scores.argsort()[::-1][:n])
    return " ".join(sentences[i] for i in top_idx)


# ---------------------------------------------------------------------------
# Transformers abstractive summariser
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_hf_pipeline(model_name: str):
    from transformers import pipeline
    logger.info("Loading HF summarisation model '%s' …", model_name)
    return pipeline("summarization", model=model_name)


def _abstractive_summary(
    text: str,
    model_name: str,
    max_length: int = 150,
    min_length: int = 40,
) -> str:
    try:
        pipe = _load_hf_pipeline(model_name)
        # HF models have input token limits; chunk if necessary
        chunk = text[:3000]
        result = pipe(chunk, max_length=max_length, min_length=min_length, do_sample=False)
        return result[0]["summary_text"].strip()
    except Exception as exc:
        logger.warning("Abstractive summarisation failed (%s), falling back to extractive", exc)
        return _extractive_summary(text, max_sentences=5)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarise_text(
    text: str,
    backend: str = "extractive",
    model_name: str = "sshleifer/distilbart-cnn-12-6",
    max_length: int = 150,
    min_length: int = 40,
) -> str:
    if not text.strip():
        return ""
    if backend == "transformers":
        return _abstractive_summary(text, model_name, max_length, min_length)
    return _extractive_summary(text, max_sentences=5)


def summarise_transcript(
    segments: list[dict[str, Any]],
    backend: str = "extractive",
    model_name: str = "sshleifer/distilbart-cnn-12-6",
    max_length: int = 150,
    min_length: int = 40,
) -> str:
    """Produce a single summary for the full transcript."""
    full_text = " ".join(s["text"] for s in segments if s.get("text"))
    return summarise_text(full_text, backend, model_name, max_length, min_length)


def summarise_chapters(
    segments: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    backend: str = "extractive",
    model_name: str = "sshleifer/distilbart-cnn-12-6",
) -> list[dict[str, Any]]:
    """
    Produce a summary for each chapter.

    Returns a list of dicts:
      ``{"title": str, "start": float, "end": float, "summary": str}``
    """
    result = []
    for ch in chapters:
        ch_segs = [
            s for s in segments
            if s["start"] >= ch["start"] and s["end"] <= ch["end"] + 0.5
        ]
        text = " ".join(s["text"] for s in ch_segs if s.get("text"))
        summary = summarise_text(text, backend, model_name) if text.strip() else "No content."
        result.append({
            "title": ch["title"],
            "start": ch["start"],
            "end": ch["end"],
            "summary": summary,
        })
    return result


def save_summary(job_id: str, payload: dict, summary_dir: Path) -> Path:
    summary_dir.mkdir(parents=True, exist_ok=True)
    out = summary_dir / f"{job_id}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return out


def load_summary(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Summary not found: {path}")
    return json.loads(path.read_text())
