from fastapi import APIRouter, HTTPException
from pathlib import Path

from backend.app.core.ingest import ingest_video
from backend.app.core.transcribe import transcribe_video, save_transcript
from backend.app.core.config import VIDEO_DIR ,CHAPTER_DIR,TRANSCRIPT_DIR  # ✅ FIX
from backend.app.core.segment import segment_chapters, load_transcript
import json

router = APIRouter()

@router.post("/ingest")
def ingest(url: str):
    try:
        result = ingest_video(url)
        return {
            "status": "downloaded",
            "job": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
def transcribe(job_id: str):
    video_path = VIDEO_DIR / f"{job_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    segments = transcribe_video(video_path)
    transcript_path = save_transcript(job_id, segments)

    return {
        "status": "transcribed",
        "segments": len(segments),
        "transcript_path": str(transcript_path)
    }

@router.post("/segment")
def segment(job_id: str):
    transcript_path = TRANSCRIPT_DIR / f"{job_id}.json"

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")

    segments = load_transcript(transcript_path)
    chapters = segment_chapters(segments)

    out_path = CHAPTER_DIR / f"{job_id}.json"
    with open(out_path, "w") as f:
        json.dump(chapters, f, indent=2)

    return {
        "status": "segmented",
        "chapters": len(chapters),
        "chapter_path": str(out_path)
    }
