from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    file_path: str
    target_lang: str
    lang_code: str
    generate_audio: bool = False
    replace_original: bool = False

class Job(JobCreate):
    id: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Setting(BaseModel):
    key: str
    value: str

    class Config:
        orm_mode = True
