import os
import subprocess
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import threading

from . import crud, models, schemas
from .database import SessionLocal, engine
from sqlalchemy import inspect, text
from .watcher import start_watcher

models.Base.metadata.create_all(bind=engine)

# Basic SQLite migration for schema updates
inspector = inspect(engine)
if "jobs" in inspector.get_table_names():
    columns = [col["name"] for col in inspector.get_columns("jobs")]
    if "replace_original" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN replace_original BOOLEAN DEFAULT 0"))
            conn.commit()

app = FastAPI(title="Translatarr")
executors = {
    'default': ThreadPoolExecutor(1)
}
scheduler = BackgroundScheduler(executors=executors)

os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_job_sync(job_id: int):
    # This runs in a background thread by APScheduler
    db = SessionLocal()
    job = crud.get_job(db, job_id)
    if not job:
        db.close()
        return

    crud.update_job_status(db, job_id, "Processing")
    try:
        # Retrieve settings for API key and models
        api_key = crud.get_setting(db, "openai_api_key", os.environ.get("OPENAI_API_KEY", ""))
        llm_model = crud.get_setting(db, "llm_model", "gpt-3.5-turbo")
        base_url = crud.get_setting(db, "base_url", "")
        tts_voice = crud.get_setting(db, "tts_voice", "es-ES-AlvaroNeural")
        llm_temperature = crud.get_setting(db, "llm_temperature", "0.3")
        llm_system_prompt = crud.get_setting(db, "llm_system_prompt", "")
        
        cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
        
        cmd = [
            "python3", cli_path, job.file_path,
            "--lang", job.target_lang,
            "--lang-code", job.lang_code,
            "--llm-model", llm_model
        ]
        if api_key:
            cmd.extend(["--api-key", api_key])
        if base_url:
            cmd.extend(["--base-url", base_url])
        if llm_temperature:
            cmd.extend(["--temperature", llm_temperature])
        if llm_system_prompt:
            cmd.extend(["--system-prompt", llm_system_prompt])
        if job.generate_audio:
            cmd.extend(["--generate-audio", "--voice", tts_voice])
        if job.replace_original:
            cmd.append("--replace-original")
            
        subprocess.run(cmd, check=True)
        crud.update_job_status(db, job_id, "Completed")
    except subprocess.CalledProcessError as e:
        crud.update_job_status(db, job_id, "Failed", error_message=f"Command failed with exit code {e.returncode}")
    except Exception as e:
        crud.update_job_status(db, job_id, "Failed", error_message=str(e))
    finally:
        db.close()

def run_job_in_scheduler(job_id: int):
    scheduler.add_job(process_job_sync, args=[job_id], id=f"job_{job_id}", replace_existing=True)

@app.on_event("startup")
def start_scheduler():
    scheduler.start()
    # Start directory watcher
    app.state.watcher = start_watcher("/movies")
    
    # On startup, requeue any jobs that were stuck in "Queued" or "Processing"
    db = SessionLocal()
    stuck_jobs = db.query(models.Job).filter(models.Job.status.in_(["Queued", "Processing"])).all()
    for job in stuck_jobs:
        crud.update_job_status(db, job.id, "Queued")
        run_job_in_scheduler(job.id)
    db.close()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    if hasattr(app.state, "watcher"):
        app.state.watcher.stop()
        app.state.watcher.join()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    jobs = crud.get_jobs(db)
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})

@app.post("/add")
async def add_job(
    file_path: str = Form(...),
    lang: str = Form(...),
    lang_code: str = Form(...),
    generate_audio: str = Form(None),
    replace_original: str = Form(None),
    db: Session = Depends(get_db)
):
    job_create = schemas.JobCreate(
        file_path=file_path,
        target_lang=lang,
        lang_code=lang_code,
        generate_audio=(generate_audio == "true"),
        replace_original=(replace_original == "true")
    )
    job = crud.create_job(db, job_create)
    run_job_in_scheduler(job.id)
    return HTMLResponse(content=f"<script>window.location.href='/';</script>")

@app.post("/delete/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    crud.delete_job(db, job_id)
    return HTMLResponse(content=f"<script>window.location.href='/';</script>")

@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request, db: Session = Depends(get_db)):
    settings = crud.get_all_settings(db)
    return templates.TemplateResponse("settings.html", {"request": request, "settings": settings})

@app.post("/settings")
async def save_settings(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    for key, value in form_data.items():
        crud.set_setting(db, key, str(value))
    return HTMLResponse(content=f"<script>window.location.href='/settings';</script>")

@app.post("/api/webhook")
async def sonarr_radarr_webhook(
    payload: dict,
    db: Session = Depends(get_db)
):
    # Extracts file path from standard Radarr/Sonarr JSON webhook payloads
    file_path = ""
    if "movie" in payload and "folderPath" in payload.get("movie", {}):
        file_path = os.path.join(payload["movie"]["folderPath"], payload.get("movieFile", {}).get("relativePath", ""))
    elif "series" in payload and "path" in payload.get("series", {}):
        file_path = os.path.join(payload["series"]["path"], payload.get("episodeFile", {}).get("relativePath", ""))
    
    if not file_path or not file_path.endswith(".mkv"):
        return {"status": "ignored", "reason": "No valid MKV file path found in payload"}
        
    target_lang = crud.get_setting(db, "auto_lang", "Spanish")
    lang_code = crud.get_setting(db, "auto_lang_code", "spa")
    generate_audio = crud.get_setting(db, "auto_generate_audio", "false").lower() == "true"
    
    job_create = schemas.JobCreate(
        file_path=file_path,
        target_lang=target_lang,
        lang_code=lang_code,
        generate_audio=generate_audio
    )
    job = crud.create_job(db, job_create)
    run_job_in_scheduler(job.id)
    return {"status": "queued", "job_id": job.id, "file": file_path}

