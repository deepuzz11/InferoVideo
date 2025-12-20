from fastapi import FastAPI
from backend.app.api.routes import router

app = FastAPI(
    title="InferaVideo",
    description="Inference-driven video intelligence platform",
    version="0.1.0"
)

@app.get("/")
def health():
    return {"status": "InferaVideo backend running"}

app.include_router(router)
