from pathlib import Path
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

# config.py is at: <project_root>/backend/app/core/config.py
# parents[0]=core, parents[1]=app, parents[2]=backend, parents[3]=project_root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "InferaVideo"
    version: str = "1.0.0"
    debug: bool = False

    # Whisper
    whisper_model: str = "base"

    # Search
    search_backend: str = "tfidf"          # "tfidf" | "embeddings"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Pipeline tuning
    highlight_threshold: float = 0.75
    chapter_window_size: int = 5
    chapter_threshold: float = 1.3
    max_clip_duration: int = 60
    merge_gap_seconds: float = 3.0

    # Summarisation
    summarise_backend: str = "extractive"  # "extractive" | "transformers"
    summarise_model: str = "sshleifer/distilbart-cnn-12-6"
    summary_max_length: int = 150
    summary_min_length: int = 40

    @property
    def base_dir(self) -> Path:
        return _PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        return _PROJECT_ROOT / "data"

    @property
    def video_dir(self) -> Path:
        return self.data_dir / "videos"

    @property
    def transcript_dir(self) -> Path:
        return self.data_dir / "transcripts"

    @property
    def chapter_dir(self) -> Path:
        return self.data_dir / "chapters"

    @property
    def highlight_dir(self) -> Path:
        return self.data_dir / "highlights"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def summary_dir(self) -> Path:
        return self.data_dir / "summaries"

    @property
    def insights_dir(self) -> Path:
        return self.data_dir / "insights"

    def ensure_dirs(self):
        for d in [
            self.video_dir, self.transcript_dir, self.chapter_dir,
            self.highlight_dir, self.jobs_dir, self.summary_dir,
            self.insights_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_prefix = "INFRA_"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s