from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def is_informative(text, min_words=6):
    return len(text.split()) >= min_words


def search_segments(segments, query: str, top_k: int = 5):
    texts = [s["text"].lower() for s in segments]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    X = vectorizer.fit_transform(texts)
    q = vectorizer.transform([query.lower()])

    scores = cosine_similarity(q, X).flatten()

    # ✅ CRITICAL: detect no semantic match
    if scores.max() == 0:
        return []

    ranked = scores.argsort()[::-1]

    results = []
    for idx in ranked:
        s = segments[idx]

        # Filter low-information segments (lyrics, fillers, etc.)
        if not is_informative(s["text"]):
            continue

        results.append({
            "text": s["text"],
            "start": s["start"],
            "end": s["end"],
            "score": float(scores[idx])
        })

        if len(results) == top_k:
            break

    return results
