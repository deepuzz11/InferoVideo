import subprocess
import uuid
from pathlib import Path

DATA_DIR = Path("data/videos")

def ingest_video(url: str):
    job_id = str(uuid.uuid4())
    output_path = DATA_DIR / f"{job_id}.mp4"

    cmd = [
        "yt-dlp",
        "-f", "mp4",
        "-o", str(output_path),
        url
    ]

    subprocess.run(cmd, check=True)
    return job_id
