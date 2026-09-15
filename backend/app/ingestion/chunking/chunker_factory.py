from app.ingestion.chunking.base import ChunkingStrategy
from app.ingestion.chunking.policy_chunker import PolicyChunker
from app.ingestion.chunking.spreadsheet_chunker import SpreadsheetChunker
from app.config.settings import settings


class ChunkerFactory:
    @classmethod
    def get_chunker(cls, source_type: str) -> ChunkingStrategy:
        if source_type in ("xlsx", "xls", "csv"):
            return SpreadsheetChunker(
                target_tokens=settings.TARGET_CHUNK_TOKENS,
            )
        return PolicyChunker(
            target_tokens=settings.TARGET_CHUNK_TOKENS,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )
