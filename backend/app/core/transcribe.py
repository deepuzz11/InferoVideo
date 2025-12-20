import whisper
from pathlib import Path

model = whisper.load_model("base")

def transcribe(video_path: Path):
    result = model.transcribe(str(video_path))
    return result["segments"]
