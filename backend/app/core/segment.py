from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def segment_chapters(segments, window_size=5):
    texts = [s["text"] for s in segments]
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    scores = np.array(X.sum(axis=1)).flatten()

    chapters = []
    current = {"start": segments[0]["start"], "texts": []}

    for i, score in enumerate(scores):
        current["texts"].append(texts[i])
        if score > scores.mean() * 1.5:
            current["end"] = segments[i]["end"]
            chapters.append(current)
            current = {"start": segments[i]["end"], "texts": []}

    return chapters
