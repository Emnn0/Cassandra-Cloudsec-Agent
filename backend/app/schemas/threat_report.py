from typing import Literal
from pydantic import BaseModel, Field


OWASP_CATEGORIES = [
    "A01:2021-Broken Access Control",
    "A02:2021-Cryptographic Failures",
    "A03:2021-Injection",
    "A04:2021-Insecure Design",
    "A05:2021-Security Misconfiguration",
    "A06:2021-Vulnerable and Outdated Components",
    "A07:2021-Identification and Authentication Failures",
    "A08:2021-Software and Data Integrity Failures",
    "A09:2021-Security Logging and Monitoring Failures",
    "A10:2021-Server-Side Request Forgery",
    "other",
]

ThreatLevelType = Literal["low", "medium", "high", "critical"]


class IdentifiedThreat(BaseModel):
    threat_type: str = Field(
        description="One of the OWASP Top 10 category strings or 'other'."
    )
    description: str = Field(
        description="Plain-English description of the threat observed."
    )
    affected_assets: list[str] = Field(
        description="IPs, URIs, or rule IDs involved in this threat."
    )
    evidence: str = Field(
        description="Specific data points from the heuristic report supporting this finding."
    )
    recommended_action: str = Field(
        description="Concrete remediation step (e.g. block IP, add WAF rule)."
    )


class InvestigationItem(BaseModel):
    entity: str
    reason: str


class ThreatReport(BaseModel):
    """Structured output produced by the LLM reasoning layer."""

    executive_summary: str = Field(
        description="2-3 sentence summary for a non-technical audience."
    )
    threat_level: ThreatLevelType = Field(
        description="Overall threat assessment: low, medium, high, or critical."
    )
    confidence_score: int = Field(
        ge=0,
        le=100,
        description="Analyst confidence in the assessment (0-100).",
    )
    identified_threats: list[IdentifiedThreat] = Field(
        description="List of distinct threats identified in the log data."
    )
    false_positive_warnings: list[str] = Field(
        description="Patterns that look suspicious but may be benign."
    )
    suggested_waf_rules: list[str] = Field(
        description="Concrete Cloudflare WAF rule suggestions."
    )
    investigation_priority: list[InvestigationItem] = Field(
        description="Ordered list of entities to investigate first."
    )
