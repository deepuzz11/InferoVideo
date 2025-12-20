from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import json
from pathlib import Path

def load_transcript(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def segment_chapters(segments, window_size=5, threshold=1.3):
    texts = [s["text"] for s in segments]

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    scores = np.asarray(X.sum(axis=1)).flatten()
    mean_score = scores.mean()

    chapters = []
    current = {
        "start": segments[0]["start"],
        "texts": []
    }

    for i, score in enumerate(scores):
        current["texts"].append(texts[i])

        if score > mean_score * threshold and i > window_size:
            current["end"] = segments[i]["end"]
            chapters.append({
                "start": current["start"],
                "end": current["end"],
                "title": " ".join(current["texts"][:3])[:60] + "..."
            })
            current = {
                "start": segments[i]["end"],
                "texts": []
            }

    current["end"] = segments[-1]["end"]
    chapters.append({
        "start": current["start"],
        "end": current["end"],
        "title": " ".join(current["texts"][:3])[:60] + "..."
    })

    return chapters
