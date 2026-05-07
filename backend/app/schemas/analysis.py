from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AnalysisCreate(BaseModel):
    log_file_id: int


class AnalysisRead(BaseModel):
    id: int
    log_file_id: int
    status: str
    progress_step: int = 0
    started_at: datetime | None
    completed_at: datetime | None
    heuristic_report: dict[str, Any] | None
    threat_report: dict[str, Any] | None
    error_message: str | None

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    items: list[AnalysisRead]
    total: int
    page: int
    page_size: int
