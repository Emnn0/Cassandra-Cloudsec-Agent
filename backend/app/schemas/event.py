from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


ActionType = Literal["block", "challenge", "allow", "log"]


class NormalizedEvent(BaseModel):
    """Unified log event schema — all parsers produce this shape."""

    timestamp: datetime
    source_ip: str
    action: ActionType
    rule_id: str | None = None
    rule_message: str | None = None
    uri: str
    method: str
    country: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    ja3_hash: str | None = None
    raw_data: dict = Field(default_factory=dict)

    model_config = {"frozen": True}
