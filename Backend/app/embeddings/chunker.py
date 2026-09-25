"""Phase 6 Semantic Chunker.

Preserves document meaning by respecting section boundaries, headings, paragraphs,
and sentence structure rather than performing naive character slicing.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from .config import EmbeddingConfig, default_embedding_config
from .metadata import compute_content_hash, generate_deterministic_chunk_id
from .models import SemanticChunk

# Heading regex: Markdown headers (#, ##, ###), Section labels, or ALL-CAPS titles
HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+|SECTION\s+\d+:?|CHAPTER\s+\d+:?|[A-Z0-9\s\-_]{4,60}:?\s*$)",
    re.MULTILINE,
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def estimate_token_count(text: str) -> int:
    """Approximate token count from whitespace words & character heuristics."""
    words = (text or "").split()
    return max(1, int(len(words) * 1.3)) if words else 0


class SemanticChunker:
    """Semantic chunking engine preserving section context and paragraph coherence."""

    def __init__(self, config: Optional[EmbeddingConfig] = None) -> None:
        self.config = config or default_embedding_config

    def _split_into_sections(self, text: str) -> List[Tuple[str, str]]:
        """Split document text into (section_title, section_body) tuples."""
        matches = list(HEADING_RE.finditer(text))
        if not matches:
            return [("Main", text.strip())]

        sections: List[Tuple[str, str]] = []
        # Leading content before first header
        if matches[0].start() > 0:
            first_body = text[: matches[0].start()].strip()
            if first_body:
                sections.append(("Introduction", first_body))

        for idx, match in enumerate(matches):
            title = match.group(0).strip().lstrip("#").strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            sections.append((title or "Section", body))

        return sections

    def _split_into_paragraphs(self, section_body: str) -> List[str]:
        """Split section text into paragraphs on blank lines."""
        raw_paras = [p.strip() for p in section_body.split("\n\n") if p.strip()]
        if not raw_paras:
            raw_paras = [p.strip() for p in section_body.split("\n") if p.strip()]
        return raw_paras if raw_paras else [section_body.strip()]

    def chunk_text(
        self,
        text: str,
        document_id: str = "doc_001",
        page_texts: Optional[Dict[int, str]] = None,
    ) -> List[SemanticChunk]:
        """Produce semantic chunks from raw document text or page-separated text."""
        clean_text = (text or "").strip()
        if not clean_text:
            return []

        chunks: List[SemanticChunk] = []

        # Step 1: Section-aware paragraph grouping
        sections = self._split_into_sections(clean_text)

        global_chunk_idx = 0

        for sec_title, sec_body in sections:
            if not sec_body:
                continue

            paragraphs = self._split_into_paragraphs(sec_body)
            current_buffer: List[str] = []
            current_len = 0

            for para in paragraphs:
                para_len = len(para)

                # If paragraph itself exceeds max_chunk_size, split by sentences
                if para_len > self.config.max_chunk_size:
                    # Flush current buffer first
                    if current_buffer:
                        combined_text = "\n\n".join(current_buffer).strip()
                        if len(combined_text) >= self.config.min_chunk_size:
                            ch_hash = compute_content_hash(combined_text)
                            cid = generate_deterministic_chunk_id(document_id, global_chunk_idx, ch_hash)
                            chunks.append(
                                SemanticChunk(
                                    chunk_id=cid,
                                    document_id=document_id,
                                    text=combined_text,
                                    section=sec_title,
                                    chunk_index=global_chunk_idx,
                                    char_count=len(combined_text),
                                    token_count=estimate_token_count(combined_text),
                                    content_hash=ch_hash,
                                )
                            )
                            global_chunk_idx += 1
                        current_buffer = []
                        current_len = 0

                    # Sentence-level fallback for large paragraph
                    sentences = SENTENCE_SPLIT_RE.split(para)
                    s_buffer: List[str] = []
                    s_len = 0

                    for sent in sentences:
                        if s_len + len(sent) > self.config.chunk_size and s_buffer:
                            c_text = " ".join(s_buffer).strip()
                            if len(c_text) >= self.config.min_chunk_size:
                                ch_hash = compute_content_hash(c_text)
                                cid = generate_deterministic_chunk_id(document_id, global_chunk_idx, ch_hash)
                                chunks.append(
                                    SemanticChunk(
                                        chunk_id=cid,
                                        document_id=document_id,
                                        text=c_text,
                                        section=sec_title,
                                        chunk_index=global_chunk_idx,
                                        char_count=len(c_text),
                                        token_count=estimate_token_count(c_text),
                                        content_hash=ch_hash,
                                    )
                                )
                                global_chunk_idx += 1
                            # Overlap: keep last sentence
                            s_buffer = s_buffer[-1:] if len(s_buffer) > 1 else []
                            s_len = sum(len(s) for s in s_buffer)

                        s_buffer.append(sent)
                        s_len += len(sent)

                    if s_buffer:
                        c_text = " ".join(s_buffer).strip()
                        if len(c_text) >= self.config.min_chunk_size:
                            ch_hash = compute_content_hash(c_text)
                            cid = generate_deterministic_chunk_id(document_id, global_chunk_idx, ch_hash)
                            chunks.append(
                                SemanticChunk(
                                    chunk_id=cid,
                                    document_id=document_id,
                                    text=c_text,
                                    section=sec_title,
                                    chunk_index=global_chunk_idx,
                                    char_count=len(c_text),
                                    token_count=estimate_token_count(c_text),
                                    content_hash=ch_hash,
                                )
                            )
                            global_chunk_idx += 1

                # If paragraph fits into current buffer
                elif current_len + para_len <= self.config.chunk_size:
                    current_buffer.append(para)
                    current_len += para_len
                else:
                    # Flush buffer as a chunk
                    combined_text = "\n\n".join(current_buffer).strip()
                    if len(combined_text) >= self.config.min_chunk_size:
                        ch_hash = compute_content_hash(combined_text)
                        cid = generate_deterministic_chunk_id(document_id, global_chunk_idx, ch_hash)
                        chunks.append(
                            SemanticChunk(
                                chunk_id=cid,
                                document_id=document_id,
                                text=combined_text,
                                section=sec_title,
                                chunk_index=global_chunk_idx,
                                char_count=len(combined_text),
                                token_count=estimate_token_count(combined_text),
                                content_hash=ch_hash,
                            )
                        )
                        global_chunk_idx += 1

                    # Start new buffer with overlap if requested
                    overlap_para = current_buffer[-1] if current_buffer and self.config.chunk_overlap > 0 else ""
                    if overlap_para and len(overlap_para) <= self.config.chunk_overlap:
                        current_buffer = [overlap_para, para]
                        current_len = len(overlap_para) + para_len
                    else:
                        current_buffer = [para]
                        current_len = para_len

            # Flush remaining section buffer
            if current_buffer:
                combined_text = "\n\n".join(current_buffer).strip()
                if len(combined_text) >= self.config.min_chunk_size:
                    ch_hash = compute_content_hash(combined_text)
                    cid = generate_deterministic_chunk_id(document_id, global_chunk_idx, ch_hash)
                    chunks.append(
                        SemanticChunk(
                            chunk_id=cid,
                            document_id=document_id,
                            text=combined_text,
                            section=sec_title,
                            chunk_index=global_chunk_idx,
                            char_count=len(combined_text),
                            token_count=estimate_token_count(combined_text),
                            content_hash=ch_hash,
                        )
                    )
                    global_chunk_idx += 1

        # Attach page_start / page_end pointers if page_texts mapping provided
        if page_texts:
            for chunk in chunks:
                for page_num in sorted(page_texts.keys()):
                    if page_texts[page_num] and chunk.text[:50] in page_texts[page_num]:
                        chunk.page_start = page_num
                        chunk.page_end = page_num
                        break

        return chunks


__all__ = ["SemanticChunker", "estimate_token_count"]
