"""
RAG-ALL: Text Chunker
Chia text thành các chunks phù hợp cho embedding và retrieval.

Chunking Strategies:
  - Fixed-size: Chia theo số ký tự/tokens
  - Sentence-based: Chia theo câu
  - Paragraph-based: Chia theo đoạn
  - Markdown-aware: respects markdown structure
"""

import re
from shared.utils.logger import rag_logger as logger


class TextChunker:
    """
    Text chunking cho RAG pipeline.

    Default: Fixed-size chunks with overlap.
    Supports markdown-aware chunking.
    """

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        strategy: str = "fixed",
    ) -> list[dict]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Input text
            chunk_size: Maximum chunk size (characters)
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy ("fixed", "sentence", "markdown")

        Returns:
            List of {"text": str, "index": int, "start": int, "end": int}
        """
        if not text or not text.strip():
            return []

        # Clean text
        text = self._clean_text(text)

        if strategy == "markdown":
            return self._chunk_markdown(text, chunk_size, chunk_overlap)
        elif strategy == "sentence":
            return self._chunk_sentences(text, chunk_size, chunk_overlap)
        else:
            return self._chunk_fixed(text, chunk_size, chunk_overlap)

    def _chunk_fixed(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[dict]:
        """
        Fixed-size chunking with overlap.
        Simple and predictable.
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at a natural boundary
            if end < len(text):
                # Look for sentence end
                for sep in ["\n\n", "\n", ". ", "! ", "? "]:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > chunk_size * 0.5:  # At least half the chunk
                        end = start + last_sep + len(sep)
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "index": chunk_index,
                    "start": start,
                    "end": end,
                })
                chunk_index += 1

            # Move start with overlap
            start = end - overlap
            if start <= chunks[-1]["start"] if chunks else 0:
                start = end  # Prevent infinite loop

        return chunks

    def _chunk_sentences(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[dict]:
        """
        Sentence-based chunking.
        Groups sentences into chunks up to chunk_size.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > chunk_size and current_chunk:
                # Flush current chunk
                chunk_text = " ".join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "index": chunk_index,
                        "start": 0,  # Approximate
                        "end": 0,
                    })
                    chunk_index += 1

                # Start new chunk with overlap (last few sentences)
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    if overlap_size + len(s) > overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s)

                current_chunk = overlap_sentences
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "index": chunk_index,
                    "start": 0,
                    "end": len(text),
                })

        return chunks

    def _chunk_markdown(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[dict]:
        """
        Markdown-aware chunking.
        Respects headers and paragraph structure.
        """
        # Split by headers (## or ###)
        sections = re.split(r'(?=^#{1,3}\s)', text, flags=re.MULTILINE)

        chunks = []
        chunk_index = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section is small enough, keep as one chunk
            if len(section) <= chunk_size:
                chunks.append({
                    "text": section,
                    "index": chunk_index,
                    "start": 0,
                    "end": len(section),
                })
                chunk_index += 1
            else:
                # Split large section using fixed chunking
                sub_chunks = self._chunk_fixed(section, chunk_size, overlap)
                for sc in sub_chunks:
                    sc["index"] = chunk_index
                    chunks.append(sc)
                    chunk_index += 1

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean text before chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n ', '\n', text)
        return text.strip()
