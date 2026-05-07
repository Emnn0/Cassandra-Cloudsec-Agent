from datetime import datetime
from pydantic import BaseModel


class PresignedUploadResponse(BaseModel):
    upload_url: str
    s3_key: str
    log_file_id: int
    expires_in_seconds: int = 900


class DirectUploadResponse(BaseModel):
    log_file_id: int
    filename: str
    size_bytes: int
    s3_key: str
    storage: str  # "s3" veya "local"


class LogFileRead(BaseModel):
    id: int
    filename: str
    s3_key: str
    size_bytes: int
    source_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
