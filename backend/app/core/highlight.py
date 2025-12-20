def extract_highlights(segments, threshold=1.3):
    avg_len = sum(len(s["text"]) for s in segments) / len(segments)

    highlights = [
        s for s in segments
        if len(s["text"]) > avg_len * threshold
    ]
    return highlights
