"""
ChunkingService — splits parsed document text into overlapping chunks.

Uses a simple whitespace-token approximation (1 token ~= 1 word) rather than
a tokenizer library, keeping the module dependency-free. Good enough for
chunk-size control; the embedding provider decides how it wants to consume
the resulting text.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    content: str
    token_count: int


class ChunkingService:
    def __init__(self, chunk_size_tokens: int = 400, chunk_overlap_tokens: int = 50) -> None:
        if chunk_overlap_tokens >= chunk_size_tokens:
            chunk_overlap_tokens = max(0, chunk_size_tokens // 4)
        self._chunk_size = chunk_size_tokens
        self._overlap = chunk_overlap_tokens

    def chunk_text(self, text: str) -> list[TextChunk]:
        tokens = (text or "").split()
        if not tokens:
            return []

        chunks: list[TextChunk] = []
        start = 0
        index = 0
        step = max(1, self._chunk_size - self._overlap)

        while start < len(tokens):
            end = min(start + self._chunk_size, len(tokens))
            piece = tokens[start:end]
            chunks.append(TextChunk(index=index, content=" ".join(piece), token_count=len(piece)))
            index += 1
            if end >= len(tokens):
                break
            start += step

        return chunks
