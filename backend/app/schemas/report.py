from datetime import datetime
from pydantic import BaseModel, Field


class TopItem(BaseModel):
    value: str
    count: int


class TopIpItem(BaseModel):
    ip: str
    count: int
    percentage: float


class TopRuleItem(BaseModel):
    rule_id: str
    rule_message: str | None
    count: int


class TimePoint(BaseModel):
    timestamp: datetime
    count: int


class Anomaly(BaseModel):
    type: str
    severity: int = Field(ge=1, le=10)
    description: str
    affected_entity: str
    supporting_data: dict = Field(default_factory=dict)


class HeuristicReport(BaseModel):
    total_events: int
    time_range: tuple[datetime, datetime]
    top_source_ips: list[TopIpItem]
    top_user_agents: list[TopItem]
    top_countries: list[TopItem]
    top_uris: list[TopItem]
    top_rules_triggered: list[TopRuleItem]
    action_distribution: dict[str, int]
    requests_per_minute: list[TimePoint]
    anomalies: list[Anomaly]
