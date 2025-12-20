from fastapi import APIRouter, HTTPException
import json

from backend.app.core.ingest import ingest_video
from backend.app.core.transcribe import transcribe_video, save_transcript
from backend.app.core.segment import segment_chapters, load_transcript
from backend.app.core.highlight import (
    score_segments, select_highlights, merge_adjacent, cut_clips
)
from backend.app.core.config import (
    VIDEO_DIR, TRANSCRIPT_DIR, CHAPTER_DIR, HIGHLIGHT_DIR
)
from backend.app.core.search import search_segments

router = APIRouter()

@router.post("/ingest")
def ingest(url: str):
    try:
        return {
            "status": "downloaded",
            "job": ingest_video(url)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
def transcribe(job_id: str):
    video_path = VIDEO_DIR / f"{job_id}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    segments = transcribe_video(video_path)
    path = save_transcript(job_id, segments)

    return {
        "status": "transcribed",
        "segments": len(segments),
        "transcript_path": str(path)
    }


@router.post("/segment")
def segment(job_id: str):
    transcript_path = TRANSCRIPT_DIR / f"{job_id}.json"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")

    segments = load_transcript(transcript_path)
    chapters = segment_chapters(segments)

    out = CHAPTER_DIR / f"{job_id}.json"
    with open(out, "w") as f:
        json.dump(chapters, f, indent=2)

    return {
        "status": "segmented",
        "chapters": len(chapters),
        "chapter_path": str(out)
    }


@router.post("/highlight")
def highlight(job_id: str):
    transcript_path = TRANSCRIPT_DIR / f"{job_id}.json"
    video_path = VIDEO_DIR / f"{job_id}.mp4"

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    segments = load_transcript(transcript_path)
    scores = score_segments(segments)
    raw = select_highlights(segments, scores)
    merged = merge_adjacent(raw)

    out_dir = HIGHLIGHT_DIR / job_id
    clips = cut_clips(video_path, merged, out_dir)

    return {
        "status": "highlights_created",
        "clips": len(clips),
        "output_dir": str(out_dir)
    }

@router.post("/search")
def search(job_id: str, query: str, top_k: int = 5):
    transcript_path = TRANSCRIPT_DIR / f"{job_id}.json"

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")

    segments = load_transcript(transcript_path)
    results = search_segments(segments, query, top_k)

    return {
        "status": "ok",
        "query": query,
        "results": results
    }
