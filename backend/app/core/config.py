from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = BASE_DIR / "data"

VIDEO_DIR = DATA_DIR / "videos"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
CHAPTER_DIR = DATA_DIR / "chapters"
HIGHLIGHT_DIR = DATA_DIR / "highlights"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
CHAPTER_DIR.mkdir(parents=True, exist_ok=True)
HIGHLIGHT_DIR.mkdir(parents=True, exist_ok=True)
