from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """Result of extracting plain text out of a binary document."""

    text: str
    page_count: int | None = None
    metadata: dict = field(default_factory=dict)


class DocumentParser(ABC):
    """Port for turning raw file bytes into extracted text.

    Lives in the domain layer so the application service depends on this
    abstraction rather than on pypdf / python-docx / openpyxl directly.
    Concrete implementations live in `infrastructure/`.
    """

    @abstractmethod
    def supports(self, *, file_name: str | None, mime_type: str | None) -> bool:
        """Whether this parser can handle the given file."""

    @abstractmethod
    async def parse(
        self, *, data: bytes, file_name: str | None, mime_type: str | None
    ) -> ParsedDocument:
        """Extract text (and basic metadata) from the file bytes."""
