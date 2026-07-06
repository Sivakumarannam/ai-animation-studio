"""
DocumentParserService — extracts plain text from raw uploaded bytes based
on source_type. Pure, stateless, no external dependencies except optional
pypdf/python-docx for their respective formats.
"""
from __future__ import annotations

import csv
import io
import json

from packages.core.exceptions import ValidationError

SUPPORTED_SOURCE_TYPES = frozenset(["txt", "md", "csv", "json", "pdf", "docx", "text"])


class DocumentParserService:
    """Parses raw bytes/text into plain text ready for chunking."""

    def parse(self, source_type: str, raw_bytes: bytes | None, raw_text: str | None = None) -> str:
        source_type = (source_type or "text").lower()
        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ValidationError(f"Unsupported source_type: {source_type}")

        if source_type == "text":
            return raw_text or ""

        if raw_bytes is None:
            raise ValidationError(f"raw_bytes required for source_type={source_type}")

        if source_type in ("txt", "md"):
            return raw_bytes.decode("utf-8", errors="replace")

        if source_type == "csv":
            return self._parse_csv(raw_bytes)

        if source_type == "json":
            return self._parse_json(raw_bytes)

        if source_type == "pdf":
            return self._parse_pdf(raw_bytes)

        if source_type == "docx":
            return self._parse_docx(raw_bytes)

        return raw_bytes.decode("utf-8", errors="replace")

    def _parse_csv(self, raw_bytes: bytes) -> str:
        text = raw_bytes.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        lines = [", ".join(row) for row in reader]
        return "\n".join(lines)

    def _parse_json(self, raw_bytes: bytes) -> str:
        text = raw_bytes.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _parse_pdf(self, raw_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ValidationError("PDF parsing requires the pypdf package") from e

        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    def _parse_docx(self, raw_bytes: bytes) -> str:
        try:
            import docx
        except ImportError as e:
            raise ValidationError("DOCX parsing requires the python-docx package") from e

        document = docx.Document(io.BytesIO(raw_bytes))
        paragraphs = [p.text for p in document.paragraphs]
        return "\n".join(paragraphs)
