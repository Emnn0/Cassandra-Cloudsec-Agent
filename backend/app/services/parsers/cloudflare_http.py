import json
import logging
from collections.abc import Iterator

from app.schemas.event import ActionType, NormalizedEvent
from app.services.parsers.base import BaseParser
from app.services.parsers.cloudflare_firewall import _normalise_action, _parse_timestamp

logger = logging.getLogger(__name__)

_HTTP_REQUIRED = {"EdgeResponseStatus", "ClientRequestURI"}


def _action_from_status(record: dict) -> ActionType:
    """
    HTTP requests don't carry an explicit 'Action' field.
    Treat 4xx/5xx responses as 'block', everything else as 'allow'.
    """
    status = record.get("EdgeResponseStatus", 200)
    try:
        code = int(status)
    except (TypeError, ValueError):
        return "allow"
    return "block" if code >= 400 else "allow"


class CloudflareHttpParser(BaseParser):
    """
    Parses Cloudflare Logpush 'http_requests' NDJSON format.

    Reference fields:
        EdgeStartTimestamp, ClientIP, EdgeResponseStatus,
        ClientRequestURI, ClientRequestMethod, ClientCountry,
        ClientRequestUserAgent, RayID, ClientSrcPort, JA3Hash
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
        return _HTTP_REQUIRED.issubset(obj.keys())

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
                        "cloudflare_http: skipping malformed line %d in %s: %s",
                        lineno,
                        file_path,
                        exc,
                    )

    def _map(self, record: dict) -> NormalizedEvent:
        raw_action = record.get("Action", "")
        action: ActionType = (
            _normalise_action(raw_action)
            if raw_action
            else _action_from_status(record)
        )
        return NormalizedEvent(
            timestamp=_parse_timestamp(
                record.get("EdgeStartTimestamp") or record["Datetime"]
            ),
            source_ip=record["ClientIP"],
            action=action,
            rule_id=record.get("RuleID") or None,
            rule_message=record.get("Description") or None,
            uri=record.get("ClientRequestURI", "/"),
            method=record.get("ClientRequestMethod", "GET"),
            country=record.get("ClientCountry") or None,
            user_agent=record.get("ClientRequestUserAgent") or None,
            request_id=record.get("RayID") or None,
            ja3_hash=record.get("JA3Hash") or None,
            raw_data=record,
        )
