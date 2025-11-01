from fastapi import FastAPI
from app.db import get_all_candidates, init_db
from app.run_sync import run_sync

app = FastAPI(title="Gmail CV Extractor API")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "Gmail CV Extractor API is running"}

@app.post("/sync")
def sync_now():
    run_sync()
    return {"status": "Sync completed"}

@app.get("/candidates")
def list_candidates():
    return get_all_candidates()