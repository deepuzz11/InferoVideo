# InferaVideo

> **Local-first video intelligence** — transcribe, search, segment, highlight, and summarise any video entirely on your own machine. No cloud APIs, no data leaves your device.

---

## Features

| Feature | Technology |
|---|---|
| Video download | `yt-dlp` (YouTube, Vimeo, 1000+ sites) |
| Transcription | OpenAI Whisper (local inference) |
| Chapter segmentation | TF-IDF boundary detection + spaCy NLP |
| Semantic search | TF-IDF cosine similarity / sentence-transformers |
| Highlight extraction | Composite TF-IDF + length + confidence scoring + ffmpeg |
| Summarisation | Extractive TextRank / HuggingFace abstractive |
| Frontend | React + Vite + Zustand |
| Backend | FastAPI + Pydantic v2 |

---

## Architecture

```
URL → yt-dlp → [video.mp4]
             → Whisper  → [transcript.json]
                        → TF-IDF segmenter → [chapters.json]
                        → Scorer + ffmpeg  → [highlight clips]
                        → Summariser       → [summary.json]

FastAPI /api/v1   ←→   React SPA (Vite, port 3000)
       /data/*         (static file serving for media)
```

Pipeline runs **asynchronously** via FastAPI `BackgroundTasks`.  
Poll `GET /api/v1/jobs/{job_id}` for real-time progress (progress_pct 0–100).

---

## Quick Start

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# ffmpeg must be on PATH
ffmpeg -version

# yt-dlp
pip install yt-dlp

# Node.js 18+ for frontend
node --version
```

### 2. Backend

```bash
# Clone / unzip project
cd inferavideo

# Install Python deps
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Copy env config
cp .env.example .env

# Start API server
uvicorn backend.app.main:app --reload --port 8000
```

API is live at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. CLI (no frontend needed)

```bash
# Full pipeline
python run_pipeline.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# With semantic search after processing
python run_pipeline.py --url <url> --query "what is machine learning" --top-k 5

# Use larger Whisper model for better accuracy
python run_pipeline.py --url <url> --whisper small

# Resume a failed job
python run_pipeline.py --job <job_id> --stages transcribe segment
```

---

## API Reference

### `POST /api/v1/process`
Start the full pipeline.
```json
{ "url": "https://www.youtube.com/watch?v=..." }
```
Returns `202 Accepted` with a `job_id`. Poll the job endpoint for progress.

### `GET /api/v1/jobs/{job_id}`
Returns full job state including per-stage status and `progress_pct`.

### `POST /api/v1/jobs/{job_id}/search`
```json
{ "query": "neural networks", "top_k": 5, "backend": "tfidf" }
```
`backend` can be `"tfidf"` (default, fast) or `"embeddings"` (semantic, requires `sentence-transformers`).

### `GET /api/v1/jobs/{job_id}/chapters`
### `GET /api/v1/jobs/{job_id}/highlights`
### `GET /api/v1/jobs/{job_id}/summary`

---

## Configuration

Edit `.env` (or set environment variables with `INFRA_` prefix):

| Variable | Default | Description |
|---|---|---|
| `INFRA_WHISPER_MODEL` | `base` | `tiny` / `base` / `small` / `medium` / `large` |
| `INFRA_SEARCH_BACKEND` | `tfidf` | `tfidf` / `embeddings` |
| `INFRA_SUMMARISE_BACKEND` | `extractive` | `extractive` / `transformers` |
| `INFRA_HIGHLIGHT_THRESHOLD` | `0.75` | 0–1, higher = fewer clips |
| `INFRA_MAX_CLIP_DURATION` | `60` | Max seconds per highlight clip |

### Semantic Search (optional)
```bash
pip install sentence-transformers
# Then set in .env:
INFRA_SEARCH_BACKEND=embeddings
```

### Abstractive Summarisation (optional)
```bash
pip install transformers torch
INFRA_SUMMARISE_BACKEND=transformers
```

---

## Running Tests

```bash
pytest tests/ -v
```

Test coverage:
- `test_search.py` — 15 unit tests (TF-IDF engine, filtering, edge cases)
- `test_segment.py` — 12 unit tests (boundary detection, title extraction)
- `test_highlight.py` — 14 unit tests (scoring, selection, merging)
- `test_summarise.py` — 16 unit tests (extractive, per-chapter, edge cases)
- `test_routes.py` — 40+ integration tests (all endpoints, error cases, validation)

---

## Project Structure

```
inferavideo/
├── backend/
│   └── app/
│       ├── api/routes.py          # All FastAPI endpoints
│       ├── core/
│       │   ├── config.py          # Settings with pydantic-settings
│       │   ├── ingest.py          # yt-dlp download
│       │   ├── transcribe.py      # Whisper transcription
│       │   ├── segment.py         # Chapter detection
│       │   ├── search.py          # TF-IDF + embedding search
│       │   ├── highlight.py       # Scoring + ffmpeg clip cutting
│       │   └── summarise.py       # Extractive + abstractive summarisation
│       ├── models/
│       │   ├── video_job.py       # Job state machine + JSON persistence
│       │   └── schemas.py         # Pydantic request/response schemas
│       ├── services/pipeline.py   # Orchestration service
│       ├── utils/time.py          # Timestamp formatting
│       └── main.py                # FastAPI app + CORS + static files
├── frontend/
│   └── src/
│       ├── components/            # Nav, VideoPlayer, JobStatus, panels
│       ├── pages/                 # HomePage, WorkspacePage, JobsPage
│       ├── hooks/                 # useJobPoller
│       ├── services/api.js        # Axios API client
│       └── store/index.js         # Zustand global state
├── tests/                         # 97 test cases
├── data/                          # Runtime data (gitignored)
├── run_pipeline.py                # CLI entry point
├── requirements.txt
├── Makefile
└── .env.example
```
---

## License

MIT © 2026
