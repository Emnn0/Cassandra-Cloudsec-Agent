from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.schemas.event import NormalizedEvent


class BaseParser(ABC):
    """
    All log format parsers implement this interface.
    Parsers MUST use generators so arbitrarily large files never fully load into memory.
    """

    @abstractmethod
    def detect(self, content_sample: bytes) -> bool:
        """
        Return True if this parser recognises the given byte sample.
        content_sample is the first 4096 bytes of the file.
        """
        ...

    @abstractmethod
    def parse(self, file_path: str) -> Iterator[NormalizedEvent]:
        """
        Yield NormalizedEvent objects one at a time.
        Malformed / unparseable lines must be skipped with a logged warning,
        never raising an exception to the caller.
        """
        ...
