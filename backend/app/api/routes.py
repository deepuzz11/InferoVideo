from fastapi import APIRouter
from app.core.ingest import ingest_video

router = APIRouter()

@router.post("/process")
def process_video(url: str):
    job = ingest_video(url)
    return {"status": "processing", "job_id": job}
