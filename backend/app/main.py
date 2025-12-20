from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.api.routes import router

app = FastAPI(
    title="InferaVideo",
    description="Inference-driven video intelligence platform",
    version="0.1.0"
)

# ✅ mount AFTER app is created
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/")
def health():
    return {"status": "InferaVideo backend running"}

app.include_router(router)
