"""Genel metin tabanlı log parser'ı — LiteSpeed, Apache, Nginx ve benzeri formatlar.

Format örneği (LiteSpeed):
  2026-05-06 00:02:47.271127 [NOTICE] [177465] [10.17.217.222:34772>88.231.63.227#host.com] [STDERR] mesaj
  2026-05-06 06:44:35.660769 [INFO] [177458] [10.17.217.222:32798] 'GET /path HTTP/1.1'

Tespit: İlk satır yyyy-mm-dd HH:MM:SS ile başlıyorsa bu parser devreye girer.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone

from app.schemas.event import ActionType, NormalizedEvent
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# 2026-05-06 00:02:47.271127 [LEVEL] [PID] [IP:port>dest#host] [CATEGORY] message
_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"   # timestamp
    r"(?:\.\d+)?\s+"                                     # microseconds (opsiyonel)
    r"\[(?P<level>[A-Z]+)\]\s+"                          # [LEVEL]
    r"\[(?P<pid>\d+)\]\s*"                               # [PID]
    r"(?:\[(?P<conn>[^\]]+)\]\s*)?"                      # [bağlantı] (opsiyonel)
    r"(?P<msg>.*)"                                       # kalan mesaj
)

# Bağlantı bloğundan IP çıkar: 10.17.217.222:34772>88.231.63.227#host.com
_CONN_RE = re.compile(r"[\d.]+:\d+>(?P<dst_ip>[\d.a-f:]+)")
_SRC_RE  = re.compile(r"^(?P<src_ip>[\d.]+):\d+")

# HTTP isteği mesaj içinde: GET /path HTTP/1.1
_HTTP_RE = re.compile(r"'?(?P<method>GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(?P<uri>/[^\s'\"]*)", re.IGNORECASE)

# Hata seviyesi → eylem eşlemi
_LEVEL_TO_ACTION: dict[str, ActionType] = {
    "ERROR":   "block",
    "WARNING": "block",
    "NOTICE":  "log",
    "INFO":    "allow",
    "DEBUG":   "allow",
    "STDERR":  "log",
    "STDOUT":  "allow",
}

# İlk satır tarih formatıyla başlıyorsa bu parser
_DETECT_RE = re.compile(rb"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


class GenericLogParser(BaseParser):
    """LiteSpeed / Apache / Nginx benzeri metin log formatlarını ayrıştırır."""

    def detect(self, content_sample: bytes) -> bool:
        if not content_sample.strip():
            return False
        first = content_sample.lstrip().split(b"\n")[0]
        return bool(_DETECT_RE.match(first))

    def parse(self, file_path: str) -> Iterator[NormalizedEvent]:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                m = _LINE_RE.match(line)
                if not m:
                    continue
                try:
                    yield self._map(m)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "generic_log: %d. satır atlandı: %s", lineno, exc
                    )

    def _map(self, m: re.Match) -> NormalizedEvent:
        ts_str = m.group("ts")
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            ts = datetime.now(timezone.utc)

        level = m.group("level").upper()
        conn  = m.group("conn") or ""
        msg   = m.group("msg").strip()

        # Kaynak IP'yi bağlantı bloğundan çıkar
        src_match = _SRC_RE.match(conn)
        source_ip = src_match.group("src_ip") if src_match else "0.0.0.0"

        # HTTP yöntemi ve URI
        http_match = _HTTP_RE.search(msg)
        method = http_match.group("method").upper() if http_match else "GET"
        uri    = http_match.group("uri")            if http_match else "/"

        # Kural mesajı: köşeli parantez içindeki kategori
        bracket_match = re.match(r"^\[([A-Z_]+)\]", msg)
        rule_message  = bracket_match.group(1) if bracket_match else None

        action: ActionType = _LEVEL_TO_ACTION.get(level, "log")

        return NormalizedEvent(
            timestamp=ts,
            source_ip=source_ip,
            action=action,
            rule_id=None,
            rule_message=rule_message,
            uri=uri,
            method=method,
            country=None,
            user_agent=None,
            request_id=m.group("pid"),
            raw_data={
                "level": level,
                "pid": m.group("pid"),
                "conn": conn,
                "message": msg[:500],
            },
        )