from __future__ import annotations

import io

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.modules.documents.domain.ocr import OcrEngine


class TesseractOcrEngine(OcrEngine):
    """OCR adapter backed by the Tesseract binary (via pytesseract).

    Requires the system packages `tesseract-ocr` (with the relevant language
    data) and `poppler-utils` (for PDF rasterisation). Both pytesseract and
    pdf2image are synchronous and CPU/IO-bound, so work is offloaded to a
    worker thread to keep the event loop responsive.
    """

    def __init__(self) -> None:
        self._default_langs = get_settings().ocr_languages
        self._dpi = get_settings().ocr_pdf_dpi

    async def image_to_text(self, data: bytes, *, languages: str | None = None) -> str:
        return await run_in_threadpool(self._image_sync, data, languages or self._default_langs)

    def _image_sync(self, data: bytes, languages: str) -> str:
        import pytesseract
        from PIL import Image

        with Image.open(io.BytesIO(data)) as img:
            return pytesseract.image_to_string(img, lang=languages).strip()

    async def pdf_to_text(self, data: bytes, *, languages: str | None = None) -> str:
        return await run_in_threadpool(self._pdf_sync, data, languages or self._default_langs)

    def _pdf_sync(self, data: bytes, languages: str) -> str:
        import pytesseract
        from pdf2image import convert_from_bytes

        pages = convert_from_bytes(data, dpi=self._dpi)
        texts: list[str] = []
        try:
            for page in pages:
                texts.append(pytesseract.image_to_string(page, lang=languages).strip())
        finally:
            for page in pages:
                page.close()
        return "\n\n".join(t for t in texts if t)
