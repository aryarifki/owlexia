"""Konektor Integrasi antara Peraturan-Crawler dan Legal AI Agent.

Membaca metadata dari /root/Peraturan-Crawler/all_pdf_metadata.json dan file PDF
untuk diindeks ke dalam basis pengetahuan RAG.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from engine.models import LegalArticle, LegalHierarchyLevel, RegulationStatus


class CrawlerConnector:
    """Connects to the Peraturan-Crawler project output."""

    def __init__(self, crawler_dir: str = "/root/Peraturan-Crawler"):
        self.crawler_dir = Path(crawler_dir)
        self.metadata_path = self.crawler_dir / "all_pdf_metadata.json"
        self.pdf_dir = self.crawler_dir / "pdf_peraturan"

    def is_crawler_available(self) -> bool:
        """Check if crawler directory exists."""
        return self.crawler_dir.exists()

    def get_crawler_stats(self) -> Dict[str, Any]:
        """Get statistics of crawled files and metadata."""
        stats = {
            "crawler_found": self.is_crawler_available(),
            "metadata_file_found": self.metadata_path.exists(),
            "total_metadata_records": 0,
            "total_downloaded_pdfs": 0,
            "pdf_dir_exists": self.pdf_dir.exists()
        }

        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stats["total_metadata_records"] = len(data) if isinstance(data, list) else 0
            except Exception as e:
                stats["metadata_read_error"] = str(e)

        if self.pdf_dir.exists():
            pdf_files = list(self.pdf_dir.glob("*.pdf"))
            stats["total_downloaded_pdfs"] = len(pdf_files)

        return stats

    def load_crawled_metadata(self) -> List[Dict[str, Any]]:
        """Load metadata records from all_pdf_metadata.json."""
        if not self.metadata_path.exists():
            return []
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
