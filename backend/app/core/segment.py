from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Title helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _best_sentence_spacy(sentences: list[str]) -> str:
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        best, best_score = sentences[0], -1
        for sent in sentences:
            doc = nlp(sent)
            score = sum(1 for chunk in doc.noun_chunks if len(chunk) >= 2)
            if score > best_score:
                best, best_score = sent, score
        return best
    except Exception:
        return _best_sentence_tfidf(sentences)


def _best_sentence_tfidf(sentences: list[str]) -> str:
    if len(sentences) == 1:
        return sentences[0]
    try:
        vec = TfidfVectorizer(stop_words="english")
        X = vec.fit_transform(sentences)
        scores = np.asarray(X.mean(axis=1)).flatten()
        return sentences[int(scores.argmax())]
    except Exception:
        return sentences[0]


def _make_title(texts: list[str], max_len: int = 72) -> str:
    sentences = [_clean(t) for t in texts if len(t.split()) >= 4]
    if not sentences:
        sentences = [_clean(t) for t in texts if t.strip()]
    if not sentences:
        return "Chapter"
    title = _best_sentence_spacy(sentences)
    if len(title) > max_len:
        idx = title.rfind(" ", 0, max_len)
        title = (title[: idx if idx > 0 else max_len]).rstrip(",.;:") + "…"
    return title


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

def segment_chapters(
    segments: list[dict[str, Any]],
    window_size: int = 5,
    threshold: float = 1.3,
) -> list[dict[str, Any]]:
    if not segments:
        return []

    texts = [s["text"] for s in segments]

    try:
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        X = vectorizer.fit_transform(texts)
        scores = np.asarray(X.sum(axis=1)).flatten()
    except ValueError:
        scores = np.ones(len(texts))

    mean_score = scores.mean()
    chapters: list[dict] = []
    current_start = segments[0]["start"]
    current_texts: list[str] = []

    for i, (seg, score) in enumerate(zip(segments, scores)):
        current_texts.append(seg["text"])
        is_boundary = (
            score > mean_score * threshold
            and i >= window_size
            and i < len(segments) - 1
        )
        if is_boundary:
            chapters.append({
                "start": current_start,
                "end": seg["end"],
                "title": _make_title(current_texts),
                "segment_count": len(current_texts),
            })
            current_start = seg["end"]
            current_texts = []

    chapters.append({
        "start": current_start,
        "end": segments[-1]["end"],
        "title": _make_title(current_texts),
        "segment_count": len(current_texts),
    })

    logger.info("Segmented into %d chapters", len(chapters))
    return chapters


def save_chapters(job_id: str, chapters: list[dict], chapter_dir: Path) -> Path:
    chapter_dir.mkdir(parents=True, exist_ok=True)
    out = chapter_dir / f"{job_id}.json"
    out.write_text(json.dumps(chapters, indent=2, ensure_ascii=False))
    return out


def load_chapters(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Chapters not found: {path}")
    return json.loads(path.read_text())
