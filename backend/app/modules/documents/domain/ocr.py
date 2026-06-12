from __future__ import annotations

from abc import ABC, abstractmethod


class OcrEngine(ABC):
    """Port for optical character recognition.

    Turns image bytes (or rasterised PDF pages) into text. Kept in the domain
    layer so the parser depends on this abstraction, not on Tesseract directly.
    Concrete implementation lives in `infrastructure/`.
    """

    @abstractmethod
    async def image_to_text(self, data: bytes, *, languages: str | None = None) -> str:
        """OCR a single raster image (PNG/JPEG/TIFF/...)."""

    @abstractmethod
    async def pdf_to_text(self, data: bytes, *, languages: str | None = None) -> str:
        """Rasterise every page of a (scanned) PDF and OCR each one."""
