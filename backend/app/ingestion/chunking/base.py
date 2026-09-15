import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import tiktoken
from app.ingestion.loaders.base import NormalizedDocument

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


@dataclass
class Chunk:
    chunk_index: int
    content: str
    token_count: int
    content_hash: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    parent_section: Optional[str] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    is_ocr: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        chunk_index: int,
        content: str,
        page_number: Optional[int] = None,
        section: Optional[str] = None,
        parent_section: Optional[str] = None,
        sheet_name: Optional[str] = None,
        row_start: Optional[int] = None,
        row_end: Optional[int] = None,
        is_ocr: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Chunk":
        token_count = count_tokens(content)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            content_hash=content_hash,
            page_number=page_number,
            section=section,
            parent_section=parent_section,
            sheet_name=sheet_name,
            row_start=row_start,
            row_end=row_end,
            is_ocr=is_ocr,
            metadata=metadata or {},
        )


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, doc: NormalizedDocument) -> List[Chunk]:
        """Split a NormalizedDocument into structured Chunks."""
        pass
