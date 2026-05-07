import logging

from app.services.parsers.base import BaseParser
from app.services.parsers.cloudflare_firewall import CloudflareFirewallParser
from app.services.parsers.cloudflare_http import CloudflareHttpParser
from app.services.parsers.generic_log import GenericLogParser

logger = logging.getLogger(__name__)

_SAMPLE_SIZE = 4096

_REGISTRY: list[BaseParser] = [
    CloudflareFirewallParser(),   # NDJSON WAF formatı — en yüksek öncelik
    CloudflareHttpParser(),        # NDJSON HTTP formatı
    GenericLogParser(),            # Metin tabanlı genel format — fallback
]


def detect_parser(file_path: str) -> BaseParser:
    """
    Read the first _SAMPLE_SIZE bytes of the file and iterate over registered
    parsers in priority order. Returns the first parser that claims the file.
    Raises ValueError if no parser recognises the format.
    """
    with open(file_path, "rb") as fh:
        sample = fh.read(_SAMPLE_SIZE)

    for parser in _REGISTRY:
        if parser.detect(sample):
            logger.debug(
                "detect_parser: %s matched %s",
                type(parser).__name__,
                file_path,
            )
            return parser

    raise ValueError(
        f"No parser found for file: {file_path!r}. "
        "Supported formats: cloudflare_firewall (NDJSON), cloudflare_http (NDJSON)."
    )
