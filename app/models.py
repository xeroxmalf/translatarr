from sqlalchemy import Column, Integer, String, Boolean, DateTime
import datetime
from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, index=True)
    target_lang = Column(String)
    lang_code = Column(String)
    generate_audio = Column(Boolean, default=False)
    replace_original = Column(Boolean, default=False)
    status = Column(String, default="Queued") # Queued, Processing, Completed, Failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)
