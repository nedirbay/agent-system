from __future__ import annotations

from abc import ABC, abstractmethod


class MetadataExtractor(ABC):
    """Port for deriving document metadata.

    Combines content statistics (word/char counts, detected language) with
    format-specific document properties (author, title, creation date, ...).
    Returns a plain JSON-serialisable dict so it can be stored directly in the
    document's `doc_metadata` column. Implemented in `infrastructure/`.
    """

    @abstractmethod
    async def extract(
        self,
        *,
        data: bytes,
        text: str,
        file_name: str | None,
        mime_type: str | None,
    ) -> dict:
        """Return a metadata dict for the given file and its extracted text."""
