from typing import List
from app.ingestion.loaders.base import NormalizedDocument
from app.ingestion.chunking.base import ChunkingStrategy, Chunk, count_tokens


class SpreadsheetChunker(ChunkingStrategy):
    def __init__(self, target_tokens: int = 512, max_tokens: int = 800):
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens

    def chunk(self, doc: NormalizedDocument) -> List[Chunk]:
        chunks: List[Chunk] = []
        chunk_idx = 0

        for table in doc.tables:
            sheet_name = table.get("sheet_name", "Sheet1")
            markdown_content = table.get("markdown", "")
            lines = markdown_content.strip().split("\n")

            if len(lines) < 3:
                continue

            header_line = lines[0]
            separator_line = lines[1]
            data_rows = lines[2:]

            current_rows: List[str] = []
            row_start = 1
            current_row_idx = 1

            for row in data_rows:
                current_rows.append(row)
                chunk_candidate = (
                    f"[{doc.title} - Sheet: {sheet_name}]\n"
                    + header_line + "\n"
                    + separator_line + "\n"
                    + "\n".join(current_rows)
                )

                if count_tokens(chunk_candidate) > self.target_tokens and len(current_rows) > 1:
                    # Pop the last row, flush the current chunk
                    last_row = current_rows.pop()
                    row_end = current_row_idx - 1

                    chunk_text = (
                        f"[{doc.title} - Sheet: {sheet_name}]\n"
                        + header_line + "\n"
                        + separator_line + "\n"
                        + "\n".join(current_rows)
                    )

                    chunks.append(
                        Chunk.create(
                            chunk_index=chunk_idx,
                            content=chunk_text,
                            sheet_name=sheet_name,
                            row_start=row_start,
                            row_end=row_end,
                            section=f"Sheet: {sheet_name}",
                            metadata={"doc_title": doc.title, "sheet_name": sheet_name},
                        )
                    )
                    chunk_idx += 1
                    current_rows = [last_row]
                    row_start = current_row_idx

                current_row_idx += 1

            # Flush remaining rows
            if current_rows:
                row_end = current_row_idx - 1
                chunk_text = (
                    f"[{doc.title} - Sheet: {sheet_name}]\n"
                    + header_line + "\n"
                    + separator_line + "\n"
                    + "\n".join(current_rows)
                )
                chunks.append(
                    Chunk.create(
                        chunk_index=chunk_idx,
                        content=chunk_text,
                        sheet_name=sheet_name,
                        row_start=row_start,
                        row_end=row_end,
                        section=f"Sheet: {sheet_name}",
                        metadata={"doc_title": doc.title, "sheet_name": sheet_name},
                    )
                )
                chunk_idx += 1

        # Fallback if no tables extracted
        if not chunks and doc.content:
            chunks.append(
                Chunk.create(
                    chunk_index=0,
                    content=doc.content,
                    section="General",
                    metadata={"doc_title": doc.title},
                )
            )

        return chunks
