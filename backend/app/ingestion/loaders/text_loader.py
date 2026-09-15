import os
from typing import Optional
from app.ingestion.loaders.base import DocumentLoader, NormalizedDocument, PageReference


class TextLoader(DocumentLoader):
    def load(self, file_path: str, original_filename: Optional[str] = None) -> NormalizedDocument:
        file_name = original_filename or os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower().lstrip(".")
        source_type = "md" if ext in ("md", "markdown") else "txt"

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        title = os.path.splitext(file_name)[0].replace("-", " ").replace("_", " ").title()

        return NormalizedDocument(
            source_file_name=file_name,
            source_type=source_type,
            title=title,
            content=content,
            sections=[],
            tables=[],
            page_references=[PageReference(page_number=1, text=content)],
            metadata={"char_count": len(content)},
        )
