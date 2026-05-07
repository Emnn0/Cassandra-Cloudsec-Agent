"""PII redaction layer for LLM inputs.

Replaces IP addresses with deterministic tokens (IP_001, IP_002 ...)
and returns the mapping so the caller can un-redact LLM responses.

Security rule: raw IPs MUST NOT reach the LLM unless redact_pii=False.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from app.schemas.report import HeuristicReport, TopIpItem

_IPV4_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)


@dataclass
class RedactionResult:
    report: HeuristicReport
    ip_mapping: dict[str, str] = field(default_factory=dict)
    reverse_mapping: dict[str, str] = field(default_factory=dict)


def redact_for_llm(
    report: HeuristicReport,
    *,
    redact_pii: bool = True,
) -> RedactionResult:
    """Return a copy of `report` with all IPs replaced by tokens.

    Args:
        report:      The heuristic report to sanitise.
        redact_pii:  When False the original report is returned unchanged
                     (for development / opt-out use cases).

    Returns:
        RedactionResult with redacted report and mappings.
    """
    if not redact_pii:
        return RedactionResult(report=report)

    ip_mapping: dict[str, str] = {}
    counter = [0]

    def _token(ip: str) -> str:
        if ip not in ip_mapping:
            counter[0] += 1
            ip_mapping[ip] = f"IP_{counter[0]:03d}"
        return ip_mapping[ip]

    def _redact_str(text: str) -> str:
        return _IPV4_RE.sub(lambda m: _token(m.group()), text)

    def _redact_anomaly_entity(entity: str) -> str:
        return _redact_str(entity)

    report_dict = report.model_dump()

    # Redact top_source_ips
    redacted_ips = []
    for item in report_dict["top_source_ips"]:
        raw_ip = item["ip"]
        redacted_ips.append({**item, "ip": _token(raw_ip)})
    report_dict["top_source_ips"] = redacted_ips

    # Redact anomalies — affected_entity + description + supporting_data
    redacted_anomalies = []
    for anomaly in report_dict["anomalies"]:
        anomaly["affected_entity"] = _redact_str(anomaly["affected_entity"])
        anomaly["description"] = _redact_str(anomaly["description"])
        anomaly["supporting_data"] = _redact_dict(anomaly["supporting_data"], _redact_str)
        redacted_anomalies.append(anomaly)
    report_dict["anomalies"] = redacted_anomalies

    reverse_mapping = {v: k for k, v in ip_mapping.items()}
    redacted_report = HeuristicReport.model_validate(report_dict)

    return RedactionResult(
        report=redacted_report,
        ip_mapping=ip_mapping,
        reverse_mapping=reverse_mapping,
    )


def unredact_text(text: str, reverse_mapping: dict[str, str]) -> str:
    """Replace IP tokens back to real IPs in LLM output text."""
    for token, real_ip in reverse_mapping.items():
        text = text.replace(token, real_ip)
    return text


def _redact_dict(data: dict, redact_fn) -> dict:
    """Recursively redact string values inside a dict."""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = redact_fn(v)
        elif isinstance(v, dict):
            result[k] = _redact_dict(v, redact_fn)
        elif isinstance(v, list):
            result[k] = [redact_fn(i) if isinstance(i, str) else i for i in v]
        else:
            result[k] = v
    return result
