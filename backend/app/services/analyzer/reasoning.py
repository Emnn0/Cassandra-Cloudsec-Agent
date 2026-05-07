"""LLM reasoning layer — converts HeuristicReport into a ThreatReport.

Pipeline:
  HeuristicReport
    -> redact_for_llm()            (strip IPs before sending to API)
    -> render Jinja2 template      (structured prompt)
    -> LLMProvider.complete()      (structured JSON output via tool_use)
    -> unredact IPs                (restore real IPs in response text)
    -> ThreatReport
"""
from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas.report import HeuristicReport
from app.schemas.threat_report import ThreatReport
from app.services.llm.provider import LLMProvider
from app.services.llm.redaction import redact_for_llm, unredact_text

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "llm"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    undefined=StrictUndefined,
    autoescape=False,
)

_SYSTEM_PROMPT = (
    "Sen 10+ yıl deneyimli kıdemli bir SOC (Güvenlik Operasyon Merkezi) analistisin. "
    "Web uygulama güvenliği ve Cloudflare WAF analizi konusunda uzmansın. "
    "Görevin: yapılandırılmış log istatistiklerini analiz edip kesin, uygulanabilir bir tehdit raporu üretmek. "
    "Tüm bulguları mümkün olduğunda OWASP Top 10 kategorileriyle eşleştir. "
    "Özlü ve somut ol; kanıtsız spekülasyondan kaçın. "
    "Tüm çıktıları Türkçe yaz."
)


async def generate_threat_report(
    heuristics: HeuristicReport,
    provider: LLMProvider,
    *,
    redact_pii: bool = True,
) -> ThreatReport:
    """Run heuristic report through the LLM and return a structured ThreatReport.

    Args:
        heuristics:   Pre-computed heuristic analysis.
        provider:     LLM provider implementation.
        redact_pii:   Whether to redact IP addresses before sending to LLM.

    Returns:
        Validated ThreatReport instance with real IPs restored.
    """
    redaction = redact_for_llm(heuristics, redact_pii=redact_pii)
    prompt = _render_prompt(redaction.report)

    logger.info(
        "reasoning.generate_threat_report: sending %d anomalies to LLM (redact_pii=%s)",
        len(heuristics.anomalies),
        redact_pii,
    )

    raw_report: ThreatReport = await provider.complete(
        prompt=prompt,
        schema=ThreatReport,
        system=_SYSTEM_PROMPT,
    )

    if redaction.reverse_mapping:
        raw_report = _unredact_report(raw_report, redaction.reverse_mapping)

    return raw_report


def _render_prompt(report: HeuristicReport) -> str:
    template = _jinja_env.get_template("threat_analysis.j2")
    time_start, time_end = report.time_range
    return template.render(
        total_events=report.total_events,
        time_range_start=time_start.strftime("%Y-%m-%d %H:%M UTC"),
        time_range_end=time_end.strftime("%Y-%m-%d %H:%M UTC"),
        top_source_ips=report.top_source_ips,
        top_user_agents=report.top_user_agents,
        top_uris=report.top_uris,
        top_countries=report.top_countries,
        top_rules=report.top_rules_triggered,
        action_distribution=report.action_distribution,
        anomalies=report.anomalies,
    )


def _unredact_report(
    report: ThreatReport,
    reverse_mapping: dict[str, str],
) -> ThreatReport:
    """Walk the ThreatReport and restore real IP addresses."""
    data = report.model_dump()

    data["executive_summary"] = unredact_text(data["executive_summary"], reverse_mapping)

    for threat in data["identified_threats"]:
        threat["description"] = unredact_text(threat["description"], reverse_mapping)
        threat["evidence"] = unredact_text(threat["evidence"], reverse_mapping)
        threat["recommended_action"] = unredact_text(threat["recommended_action"], reverse_mapping)
        threat["affected_assets"] = [
            unredact_text(a, reverse_mapping) for a in threat["affected_assets"]
        ]

    data["false_positive_warnings"] = [
        unredact_text(w, reverse_mapping) for w in data["false_positive_warnings"]
    ]
    data["suggested_waf_rules"] = [
        unredact_text(r, reverse_mapping) for r in data["suggested_waf_rules"]
    ]
    data["investigation_priority"] = [
        {"entity": unredact_text(item["entity"], reverse_mapping), "reason": item["reason"]}
        for item in data["investigation_priority"]
    ]

    return ThreatReport.model_validate(data)
