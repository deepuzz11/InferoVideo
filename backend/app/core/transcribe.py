import whisper
import json
from pathlib import Path
from backend.app.core.config import TRANSCRIPT_DIR

model = whisper.load_model("base")

def transcribe_video(video_path: Path):
    result = model.transcribe(str(video_path))
    return result["segments"]

def save_transcript(job_id: str, segments):
    out = TRANSCRIPT_DIR / f"{job_id}.json"
    with open(out, "w") as f:
        json.dump(segments, f, indent=2)
    return out
