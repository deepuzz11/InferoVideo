import subprocess
import uuid
from pathlib import Path
from backend.app.core.config import VIDEO_DIR

def ingest_video(url: str) -> dict:
    job_id = str(uuid.uuid4())
    output_path = VIDEO_DIR / f"{job_id}.mp4"

    cmd = [
        "yt-dlp",
        "-f", "mp4",
        "-o", str(output_path),
        url
    ]

    subprocess.run(cmd, check=True)

    return {
        "job_id": job_id,
        "video_path": str(output_path)
    }
