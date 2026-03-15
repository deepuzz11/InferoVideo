from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

_MIN_WORDS = 5


def _is_informative(text: str) -> bool:
    return len(text.split()) >= _MIN_WORDS


def _normalise(arr: np.ndarray) -> np.ndarray:
    mn, mx = arr.min(), arr.max()
    return (arr - mn) / (mx - mn + 1e-9)


# ---------------------------------------------------------------------------
# TF-IDF backend
# ---------------------------------------------------------------------------

def _search_tfidf(segments: list[dict], query: str, top_k: int) -> list[dict]:
    texts = [s["text"].lower() for s in segments]
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        X = vec.fit_transform(texts)
        q = vec.transform([query.lower()])
    except ValueError:
        return []

    scores = cosine_similarity(q, X).flatten()
    if scores.max() == 0:
        return []

    results = []
    for idx in scores.argsort()[::-1]:
        if not _is_informative(segments[idx]["text"]):
            continue
        if scores[idx] <= 0:
            break
        results.append({**segments[idx], "score": round(float(scores[idx]), 4), "backend": "tfidf"})
        if len(results) == top_k:
            break
    return results


# ---------------------------------------------------------------------------
# Sentence-transformer backend
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_st_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    logger.info("Loading SentenceTransformer '%s' …", model_name)
    return SentenceTransformer(model_name)


def _search_embeddings(segments: list[dict], query: str, top_k: int, model_name: str) -> list[dict]:
    try:
        model = _load_st_model(model_name)
    except Exception as exc:
        logger.warning("Embeddings unavailable (%s), falling back to TF-IDF", exc)
        return _search_tfidf(segments, query, top_k)

    texts = [s["text"] for s in segments]
    corpus_emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    query_emb = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
    scores = _normalise(cosine_similarity(query_emb, corpus_emb).flatten())

    results = []
    for idx in scores.argsort()[::-1]:
        if not _is_informative(segments[idx]["text"]):
            continue
        results.append({**segments[idx], "score": round(float(scores[idx]), 4), "backend": "embeddings"})
        if len(results) == top_k:
            break
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_segments(
    segments: list[dict[str, Any]],
    query: str,
    top_k: int = 5,
    backend: str = "tfidf",
    embedding_model: str = "all-MiniLM-L6-v2",
) -> list[dict[str, Any]]:
    if not segments or not query.strip():
        return []
    if backend == "embeddings":
        return _search_embeddings(segments, query, top_k, embedding_model)
    return _search_tfidf(segments, query, top_k)
