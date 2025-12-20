from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import subprocess
from pathlib import Path

def score_segments(segments):
    texts = [s["text"] for s in segments]

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    tfidf = np.asarray(X.sum(axis=1)).flatten()
    lengths = np.array([len(t.split()) for t in texts])

    tfidf = tfidf / (tfidf.max() + 1e-6)
    lengths = lengths / (lengths.max() + 1e-6)

    return 0.7 * tfidf + 0.3 * lengths


def select_highlights(segments, scores, threshold=0.75):
    return [
        {
            "start": s["start"],
            "end": s["end"],
            "score": float(sc)
        }
        for s, sc in zip(segments, scores)
        if sc >= threshold
    ]


def merge_adjacent(highlights, gap=3.0):
    if not highlights:
        return []

    merged = [highlights[0]]
    for h in highlights[1:]:
        last = merged[-1]
        if h["start"] - last["end"] <= gap:
            last["end"] = h["end"]
            last["score"] = max(last["score"], h["score"])
        else:
            merged.append(h)
    return merged


def cut_clips(video_path: Path, clips, out_dir: Path, max_len=60):
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for i, c in enumerate(clips):
        start = c["start"]
        duration = min(max_len, c["end"] - c["start"])
        out = out_dir / f"clip_{i+1:02d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            str(out)
        ]

        subprocess.run(cmd, check=True)
        outputs.append(str(out))

    return outputs
