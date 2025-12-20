from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoJob(BaseModel):
    job_id: str

    # Input
    source_url: Optional[str] = None

    # Artifacts
    video_path: Optional[str] = None
    transcript_path: Optional[str] = None
    chapter_path: Optional[str] = None
    highlight_dir: Optional[str] = None

    # Status
    ingest_status: str = "pending"
    transcribe_status: str = "pending"
    segment_status: str = "pending"
    highlight_status: str = "pending"

    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    error: Optional[str] = None

    def update_status(self, stage: str, status: str):
        setattr(self, f"{stage}_status", status)
        self.updated_at = datetime.utcnow()
