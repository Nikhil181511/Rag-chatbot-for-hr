import os
from typing import Dict, Type
from app.ingestion.loaders.base import DocumentLoader
from app.ingestion.loaders.pdf_loader import PDFLoader
from app.ingestion.loaders.docx_loader import DOCXLoader
from app.ingestion.loaders.text_loader import TextLoader
from app.ingestion.loaders.excel_loader import ExcelLoader


class UnsupportedFileTypeError(Exception):
    pass


class LoaderFactory:
    _loaders: Dict[str, Type[DocumentLoader]] = {
        ".pdf": PDFLoader,
        ".docx": DOCXLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".markdown": TextLoader,
        ".xlsx": ExcelLoader,
        ".xls": ExcelLoader,
        ".csv": ExcelLoader,
    }

    @classmethod
    def get_loader(cls, file_name: str) -> DocumentLoader:
        ext = os.path.splitext(file_name)[1].lower()
        loader_cls = cls._loaders.get(ext)
        if not loader_cls:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(cls._loaders.keys())}"
            )
        return loader_cls()
