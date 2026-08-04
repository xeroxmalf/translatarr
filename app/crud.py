from sqlalchemy.orm import Session
from . import models, schemas
import datetime

def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).order_by(models.Job.created_at.desc()).offset(skip).limit(limit).all()

def create_job(db: Session, job: schemas.JobCreate):
    db_job = models.Job(
        file_path=job.file_path,
        target_lang=job.target_lang,
        lang_code=job.lang_code,
        generate_audio=job.generate_audio,
        replace_original=job.replace_original,
        status="Queued"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int):
    job = get_job(db, job_id)
    if job:
        db.delete(job)
        db.commit()
    return job

def update_job_status(db: Session, job_id: int, status: str, error_message: str = None):
    job = get_job(db, job_id)
    if job:
        job.status = status
        if error_message:
            job.error_message = error_message
        if status in ["Completed", "Failed"]:
            job.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job

def get_setting(db: Session, key: str, default: str = None):
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    if setting:
        return setting.value
    return default

def set_setting(db: Session, key: str, value: str):
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = models.Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

def get_all_settings(db: Session):
    return {s.key: s.value for s in db.query(models.Setting).all()}
