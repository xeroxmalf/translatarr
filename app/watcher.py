import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .database import SessionLocal
from . import crud, schemas

logger = logging.getLogger(__name__)

class MovieHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".mkv"):
            logger.info(f"New MKV detected: {event.src_path}, waiting for transfer to complete...")
            self.wait_for_file_transfer(event.src_path)
            self.add_to_queue(event.src_path)
            
    def wait_for_file_transfer(self, file_path, timeout_secs=300):
        # Wait until the file size hasn't changed for 3 seconds
        last_size = -1
        stable_count = 0
        slept = 0
        while slept < timeout_secs:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_size = current_size
                
                if stable_count >= 3:
                    logger.info(f"File transfer complete for {file_path}")
                    return
            except OSError:
                pass
            time.sleep(1)
            slept += 1
        logger.warning(f"Timeout waiting for {file_path} to finish transferring.")

    def add_to_queue(self, file_path):
        db = SessionLocal()
        try:
            # Check if it already exists to prevent double queuing
            existing = db.query(crud.models.Job).filter(crud.models.Job.file_path == file_path).first()
            if existing:
                return

            # Default settings for auto-queued items
            target_lang = crud.get_setting(db, "auto_lang", "Spanish")
            lang_code = crud.get_setting(db, "auto_lang_code", "spa")
            generate_audio = crud.get_setting(db, "auto_generate_audio", "false").lower() == "true"
            replace_original = crud.get_setting(db, "auto_replace_original", "false").lower() == "true"

            job_create = schemas.JobCreate(
                file_path=file_path,
                target_lang=target_lang,
                lang_code=lang_code,
                generate_audio=generate_audio,
                replace_original=replace_original
            )
            job = crud.create_job(db, job_create)
            from .main import run_job_in_scheduler
            run_job_in_scheduler(job.id)
            logger.info(f"Auto-queued job for {file_path}")
        except Exception as e:
            logger.error(f"Error auto-queuing {file_path}: {e}")
        finally:
            db.close()

def start_watcher(directory="/movies"):
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    event_handler = MovieHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    return observer
