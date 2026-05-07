"""PDF report generator.

Pipeline: ThreatReport + HeuristicReport -> Jinja2 HTML -> PDF (bytes)

Backend selection (in order):
1. WeasyPrint  — preferred in production (Docker/Linux, requires GTK)
2. Playwright  — fallback for Windows dev environments
"""
from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas.report import HeuristicReport
from app.schemas.threat_report import ThreatReport

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "report"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    undefined=StrictUndefined,
    autoescape=True,
)

_THREAT_LEVEL_COLOR = {
    "low": "#22c55e",
    "medium": "#f59e0b",
    "high": "#f97316",
    "critical": "#dc2626",
}


def generate_pdf(
    threat_report: ThreatReport,
    heuristic_report: HeuristicReport,
    *,
    generated_at: datetime | None = None,
) -> bytes:
    """Render HTML template and convert to PDF bytes.

    Tries WeasyPrint first (production/Linux). Falls back to Playwright
    when WeasyPrint's native GTK dependencies are unavailable (Windows dev).
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)

    html_content = _render_html(threat_report, heuristic_report, generated_at)

    try:
        return _weasyprint_pdf(html_content)
    except Exception as wp_err:
        logger.warning("WeasyPrint unavailable (%s) — falling back to Playwright", wp_err)
        return asyncio.run(_playwright_pdf(html_content))


def _render_html(
    threat_report: ThreatReport,
    heuristic_report: HeuristicReport,
    generated_at: datetime,
) -> str:
    time_start, time_end = heuristic_report.time_range
    ctx = {
        "threat": threat_report,
        "heuristic": heuristic_report,
        "generated_at": generated_at.strftime("%B %d, %Y at %H:%M UTC"),
        "time_range_start": time_start.strftime("%Y-%m-%d %H:%M UTC"),
        "time_range_end": time_end.strftime("%Y-%m-%d %H:%M UTC"),
        "threat_level_color": _THREAT_LEVEL_COLOR.get(threat_report.threat_level, "#6b7280"),
        "confidence_pct": threat_report.confidence_score,
    }
    template = _jinja_env.get_template("threat_report.html")
    return template.render(**ctx)


def _weasyprint_pdf(html_content: str) -> bytes:
    from weasyprint import CSS, HTML  # type: ignore[import]

    css_path = _TEMPLATES_DIR / "threat_report.css"
    css = CSS(filename=str(css_path))
    pdf_bytes: bytes = HTML(string=html_content, base_url=str(_TEMPLATES_DIR)).write_pdf(
        stylesheets=[css]
    )
    logger.info("generate_pdf (WeasyPrint): %d bytes", len(pdf_bytes))
    return pdf_bytes


async def _playwright_pdf(html_content: str) -> bytes:
    from playwright.async_api import async_playwright  # type: ignore[import]

    css_path = _TEMPLATES_DIR / "threat_report.css"
    css_content = css_path.read_text(encoding="utf-8")

    full_html = html_content.replace(
        '<link rel="stylesheet" href="threat_report.css" />',
        f"<style>{css_content}</style>",
    )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(full_html)
        tmp_path = Path(f.name)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file:///{tmp_path.as_posix()}")
            await page.wait_for_load_state("networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            await browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    logger.info("generate_pdf (Playwright): %d bytes", len(pdf_bytes))
    return pdf_bytes