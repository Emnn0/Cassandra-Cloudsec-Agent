"""Quick script to generate a sample PDF report for visual verification."""
from datetime import datetime, timedelta, timezone

from app.schemas.event import NormalizedEvent
from app.schemas.threat_report import IdentifiedThreat, InvestigationItem, ThreatReport
from app.services.analyzer.heuristics import analyze
from app.services.report.generator import generate_pdf

BASE_TS = datetime(2024, 5, 1, 10, 0, 0, tzinfo=timezone.utc)

events = [
    NormalizedEvent(
        timestamp=BASE_TS + timedelta(seconds=i),
        source_ip="203.0.113.42",
        action="block",
        uri="/login",
        method="POST",
        rule_id="sqli-detect",
        rule_message="SQL Injection detected",
        country="CN",
        user_agent="python-requests/2.28",
        raw_data={},
    )
    for i in range(200)
] + [
    NormalizedEvent(
        timestamp=BASE_TS + timedelta(seconds=i + 300),
        source_ip=f"10.0.{i // 100}.{i % 100}",
        action="allow",
        uri="/api/data",
        method="GET",
        rule_id=None,
        rule_message=None,
        country="US",
        user_agent="Mozilla/5.0",
        raw_data={},
    )
    for i in range(50)
]

heuristic = analyze(events)

threat = ThreatReport(
    executive_summary=(
        "A sustained SQL injection campaign originating from a single IP (203.0.113.42) "
        "was detected, targeting the /login endpoint. Over 200 blocked requests were recorded "
        "within the observation window. Immediate IP-level blocking and parameterised query "
        "review are recommended."
    ),
    threat_level="critical",
    confidence_score=92,
    identified_threats=[
        IdentifiedThreat(
            threat_type="A03:2021-Injection",
            description=(
                "IP 203.0.113.42 sent 200 requests matching SQL injection rule sqli-detect, "
                "targeting /login."
            ),
            affected_assets=["203.0.113.42", "/login"],
            evidence=(
                "Rule sqli-detect triggered 200 times; single IP responsible for 80% of "
                "all traffic."
            ),
            recommended_action=(
                "Block 203.0.113.42 at WAF level; enforce parameterised queries on /login; "
                "add rate limiting."
            ),
        )
    ],
    false_positive_warnings=[
        "Automated security scanners (Qualys, Tenable) may trigger SQLi rules during scheduled scans."
    ],
    suggested_waf_rules=[
        "(ip.src eq 203.0.113.42) => block",
        '(http.request.uri.path eq "/login" and http.request.method eq "POST" and rate(60) gt 20) => challenge',
    ],
    investigation_priority=[
        InvestigationItem(
            entity="203.0.113.42",
            reason="Responsible for 80% of traffic and 200 SQLi rule hits.",
        ),
        InvestigationItem(
            entity="/login",
            reason="Primary targeted endpoint with 200 attack attempts.",
        ),
    ],
)

pdf_bytes = generate_pdf(threat, heuristic)
out_path = r"C:\Users\Emin\OneDrive\Desktop\loglens_sample_report.pdf"
with open(out_path, "wb") as f:
    f.write(pdf_bytes)

print(f"PDF generated: {len(pdf_bytes):,} bytes -> {out_path}")