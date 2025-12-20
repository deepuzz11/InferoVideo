from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import json
from pathlib import Path

def load_transcript(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def segment_chapters(segments, window_size=5, threshold=1.3):
    """
    segments: list of {start, end, text}
    returns: list of chapters with start/end
    """

    texts = [s["text"] for s in segments]

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    # importance score per segment
    scores = np.asarray(X.sum(axis=1)).flatten()
    mean_score = scores.mean()

    chapters = []
    current_chapter = {
        "start": segments[0]["start"],
        "texts": []
    }

    for i, score in enumerate(scores):
        current_chapter["texts"].append(texts[i])

        # topic boundary detected
        if score > mean_score * threshold and i > window_size:
            current_chapter["end"] = segments[i]["end"]
            chapters.append(current_chapter)

            current_chapter = {
                "start": segments[i]["end"],
                "texts": []
            }

    # close final chapter
    current_chapter["end"] = segments[-1]["end"]
    chapters.append(current_chapter)

    return chapters
