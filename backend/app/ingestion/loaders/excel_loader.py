import os
from typing import Optional, List, Dict, Any
import pandas as pd
from app.ingestion.loaders.base import DocumentLoader, NormalizedDocument, PageReference
from app.config.logging import get_logger

logger = get_logger(__name__)


class ExcelLoader(DocumentLoader):
    def load(self, file_path: str, original_filename: Optional[str] = None) -> NormalizedDocument:
        file_name = original_filename or os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower().lstrip(".")
        source_type = "csv" if ext == "csv" else "xlsx"

        sheet_data: Dict[str, pd.DataFrame] = {}
        if source_type == "csv":
            df = pd.read_csv(file_path)
            sheet_data["Sheet1"] = df
        else:
            # Excel workbook with multiple potential sheets
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    sheet_data[sheet_name] = df
                except Exception as e:
                    logger.warning("Failed to parse sheet in Excel file", sheet=sheet_name, error=str(e))

        content_parts: List[str] = []
        tables_extracted: List[Dict[str, Any]] = []

        for sheet_name, df in sheet_data.items():
            if df.empty:
                continue

            # Fill NaN values with empty string
            df = df.fillna("")
            headers = [str(c).strip() for c in df.columns]

            sheet_header_text = f"## Sheet: {sheet_name}\n"
            content_parts.append(sheet_header_text)

            # Build markdown table representation
            md_table = "| " + " | ".join(headers) + " |\n"
            md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

            for idx, row in df.iterrows():
                row_values = [str(val).strip() for val in row.values]
                md_table += "| " + " | ".join(row_values) + " |\n"

            content_parts.append(md_table)

            tables_extracted.append({
                "sheet_name": sheet_name,
                "row_count": len(df),
                "columns": headers,
                "markdown": md_table,
            })

        combined_content = "\n\n".join(content_parts)
        title = os.path.splitext(file_name)[0].replace("-", " ").replace("_", " ").title()

        return NormalizedDocument(
            source_file_name=file_name,
            source_type=source_type,
            title=title,
            content=combined_content,
            sections=[],
            tables=tables_extracted,
            page_references=[PageReference(page_number=1, text=combined_content)],
            metadata={"sheets": list(sheet_data.keys()), "source_type": source_type},
        )
