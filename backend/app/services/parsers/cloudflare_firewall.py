import json
import logging
from collections.abc import Iterator
from datetime import datetime, timezone

from app.schemas.event import ActionType, NormalizedEvent
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

_FIREWALL_REQUIRED = {"Action", "ClientRequestPath"}
_HTTP_EXCLUSIVE = {"EdgeResponseStatus", "EdgeStartTimestamp"}

_VALID_ACTIONS: set[str] = {"block", "challenge", "allow", "log"}


def _normalise_action(raw: str) -> ActionType:
    lower = raw.lower()
    return lower if lower in _VALID_ACTIONS else "log"  # type: ignore[return-value]


def _parse_timestamp(raw: str) -> datetime:
    """Accept RFC3339 / ISO8601 strings that Cloudflare emits."""
    raw = raw.rstrip("Z")
    if "+" in raw[10:]:
        raw = raw[: raw.rfind("+")]
    return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)


class CloudflareFirewallParser(BaseParser):
    """
    Parses Cloudflare Logpush 'firewall_events' NDJSON format.
    Each line is a self-contained JSON object.

    Reference fields:
        Datetime, ClientIP, Action, RuleID, Description,
        ClientRequestPath, ClientRequestMethod, ClientCountry,
        ClientRequestUserAgent, RayID, ClientRequestHostname, JA3Hash
    """

    def detect(self, content_sample: bytes) -> bool:
        if not content_sample.strip():
            return False
        first_line = content_sample.split(b"\n")[0].strip()
        if not (first_line.startswith(b"{") and first_line.endswith(b"}")):
            return False
        try:
            obj = json.loads(first_line)
        except json.JSONDecodeError:
            return False
        keys = obj.keys()
        has_firewall_fields = _FIREWALL_REQUIRED.issubset(keys)
        is_http_format = bool(_HTTP_EXCLUSIVE.intersection(keys))
        return has_firewall_fields and not is_http_format

    def parse(self, file_path: str) -> Iterator[NormalizedEvent]:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    event = self._map(record)
                    yield event
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "cloudflare_firewall: skipping malformed line %d in %s: %s",
                        lineno,
                        file_path,
                        exc,
                    )

    def _map(self, record: dict) -> NormalizedEvent:
        return NormalizedEvent(
            timestamp=_parse_timestamp(record["Datetime"]),
            source_ip=record["ClientIP"],
            action=_normalise_action(record.get("Action", "log")),
            rule_id=record.get("RuleID") or None,
            rule_message=record.get("Description") or None,
            uri=record.get("ClientRequestPath", "/"),
            method=record.get("ClientRequestMethod", "GET"),
            country=record.get("ClientCountry") or None,
            user_agent=record.get("ClientRequestUserAgent") or None,
            request_id=record.get("RayID") or None,
            ja3_hash=record.get("JA3Hash") or None,
            raw_data=record,
        )
