from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PageReference:
    page_number: int
    text: str


@dataclass
class NormalizedDocument:
    source_file_name: str
    source_type: str
    title: str
    content: str
    sections: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    page_references: List[PageReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_id: Optional[str] = None


class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: str, original_filename: Optional[str] = None) -> NormalizedDocument:
        """Loads and normalizes document content from the specified file path."""
        pass
