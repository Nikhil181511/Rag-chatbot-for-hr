import re
from typing import List, Optional
from app.ingestion.loaders.base import NormalizedDocument
from app.ingestion.chunking.base import ChunkingStrategy, Chunk, count_tokens


class PolicyChunker(ChunkingStrategy):
    def __init__(
        self,
        target_tokens: int = 512,
        min_tokens: int = 100,
        max_tokens: int = 800,
        overlap_tokens: int = 80,
    ):
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, doc: NormalizedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        chunk_idx = 0

        # Split content into logical paragraphs / sections
        # First check if there are page references
        if doc.page_references and len(doc.page_references) > 1:
            for pref in doc.page_references:
                page_chunks = self._chunk_text(
                    text=pref.text,
                    doc_title=doc.title,
                    page_number=pref.page_number,
                    start_index=chunk_idx,
                )
                chunks.extend(page_chunks)
                chunk_idx += len(page_chunks)
        else:
            chunks = self._chunk_text(
                text=doc.content,
                doc_title=doc.title,
                page_number=1,
                start_index=0,
            )

        return chunks

    def _chunk_text(
        self,
        text: str,
        doc_title: str,
        page_number: Optional[int],
        start_index: int,
    ) -> List[Chunk]:
        # Split by markdown headings or double newlines
        paragraphs = re.split(r"\n{2,}", text)
        chunks: List[Chunk] = []
        
        current_section = "General"
        current_tokens: List[str] = []
        current_token_count = 0
        current_chunk_idx = start_index

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Detect headings
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", para)
            if heading_match:
                current_section = heading_match.group(2).strip()

            para_tokens = count_tokens(para)

            # If a single paragraph exceeds max tokens, split by sentences
            if para_tokens > self.max_tokens:
                sentences = re.split(r"(?<=[.?!])\s+", para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    s_tokens = count_tokens(sentence)

                    if current_token_count + s_tokens > self.target_tokens and current_token_count >= self.min_tokens:
                        # Flush current chunk
                        chunk_text = f"[{doc_title}] > {current_section}\n\n" + "\n\n".join(current_tokens)
                        chunks.append(
                            Chunk.create(
                                chunk_index=current_chunk_idx,
                                content=chunk_text,
                                page_number=page_number,
                                section=current_section,
                                metadata={"doc_title": doc_title},
                            )
                        )
                        current_chunk_idx += 1
                        
                        # Apply overlap
                        overlap_paras = current_tokens[-1:] if current_tokens else []
                        current_tokens = overlap_paras + [sentence]
                        current_token_count = sum(count_tokens(p) for p in current_tokens)
                    else:
                        current_tokens.append(sentence)
                        current_token_count += s_tokens

            elif current_token_count + para_tokens > self.target_tokens and current_token_count >= self.min_tokens:
                # Flush current chunk
                chunk_text = f"[{doc_title}] > {current_section}\n\n" + "\n\n".join(current_tokens)
                chunks.append(
                    Chunk.create(
                        chunk_index=current_chunk_idx,
                        content=chunk_text,
                        page_number=page_number,
                        section=current_section,
                        metadata={"doc_title": doc_title},
                    )
                )
                current_chunk_idx += 1

                # Overlap with the last paragraph
                overlap_paras = current_tokens[-1:] if current_tokens else []
                current_tokens = overlap_paras + [para]
                current_token_count = sum(count_tokens(p) for p in current_tokens)
            else:
                current_tokens.append(para)
                current_token_count += para_tokens

        # Flush any remaining tokens
        if current_tokens:
            chunk_text = f"[{doc_title}] > {current_section}\n\n" + "\n\n".join(current_tokens)
            chunks.append(
                Chunk.create(
                    chunk_index=current_chunk_idx,
                    content=chunk_text,
                    page_number=page_number,
                    section=current_section,
                    metadata={"doc_title": doc_title},
                )
            )

        return chunks
