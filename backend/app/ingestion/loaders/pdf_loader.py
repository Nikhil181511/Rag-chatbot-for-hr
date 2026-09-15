import os
from typing import Optional, List, Dict, Any
import pdfplumber
from app.ingestion.loaders.base import DocumentLoader, NormalizedDocument, PageReference
from app.config.logging import get_logger

logger = get_logger(__name__)


class PDFLoader(DocumentLoader):
    def load(self, file_path: str, original_filename: Optional[str] = None) -> NormalizedDocument:
        file_name = original_filename or os.path.basename(file_path)
        full_text_parts: List[str] = []
        page_refs: List[PageReference] = []
        sections: List[Dict[str, Any]] = []
        tables_extracted: List[Dict[str, Any]] = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    page_num = idx + 1
                    text = page.extract_text() or ""
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    for t_idx, table in enumerate(tables):
                        if table:
                            # Format table as Markdown table
                            clean_table = [[str(cell or "").strip() for cell in row] for row in table]
                            if clean_table and len(clean_table) > 1:
                                headers = clean_table[0]
                                rows = clean_table[1:]
                                md_table = "\n| " + " | ".join(headers) + " |\n"
                                md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                                for row in rows:
                                    md_table += "| " + " | ".join(row) + " |\n"
                                tables_extracted.append({
                                    "page": page_num,
                                    "table_index": t_idx,
                                    "markdown": md_table,
                                })

                    # Clean header/footer lines (common heuristic: first/last 1-2 lines if short/page number)
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    cleaned_lines = []
                    for l_idx, line in enumerate(lines):
                        # Filter standalone page number indicators
                        if line.isdigit() and (l_idx == 0 or l_idx == len(lines) - 1):
                            continue
                        cleaned_lines.append(line)

                    page_clean_text = "\n".join(cleaned_lines)
                    if page_clean_text:
                        full_text_parts.append(f"[Page {page_num}]\n{page_clean_text}")
                        page_refs.append(PageReference(page_number=page_num, text=page_clean_text))

        except Exception as e:
            logger.error("Error reading PDF file", file_path=file_path, exc_info=e)
            raise

        combined_content = "\n\n".join(full_text_parts)
        title = os.path.splitext(file_name)[0].replace("-", " ").replace("_", " ").title()

        return NormalizedDocument(
            source_file_name=file_name,
            source_type="pdf",
            title=title,
            content=combined_content,
            sections=sections,
            tables=tables_extracted,
            page_references=page_refs,
            metadata={"total_pages": len(page_refs), "is_ocr": False},
        )
