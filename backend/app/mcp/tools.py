import os
import glob
from typing import List, Dict, Any
from app.config.settings import settings


class HRDocumentMCPTools:
    @staticmethod
    def list_uploaded_documents() -> List[Dict[str, Any]]:
        """List all files present in the designated storage/uploads directory."""
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return []
        
        files = []
        for file_path in glob.glob(os.path.join(upload_dir, "*")):
            if os.path.isfile(file_path):
                files.append({
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path),
                    "path": file_path,
                })
        return files

    @staticmethod
    def read_document_excerpt(file_name: str, max_chars: int = 2000) -> Dict[str, Any]:
        """Read text excerpt from a document in uploads directory safely."""
        # Sanitize against directory traversal
        clean_name = os.path.basename(file_name)
        file_path = os.path.join(settings.UPLOAD_DIR, clean_name)
        
        if not os.path.exists(file_path):
            return {"error": f"File {clean_name} not found in uploads directory"}

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
            return {"file_name": clean_name, "excerpt": content}
        except Exception as e:
            return {"error": str(e)}
