"""Pipeline Ingestion: Mengintegrasikan Crawler, Metadata Enricher, dan Legal Parser."""
import os
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

from engine.models import LegalArticle, LegalHierarchyLevel, RegulationStatus
from engine.parser import LegalDocumentParser
from crawler_connector.metadata_enricher import PeraturanMetadataEnricher


class LegalDataPipeline:
    """Manages downloading, parsing, and ingestion of Indonesian legislation."""

    def __init__(
        self,
        storage_dir: str = "/root/legal-ai-agent/data",
        crawler_pdf_dir: str = "/root/Peraturan-Crawler/pdf_peraturan"
    ):
        self.storage_dir = Path(storage_dir)
        self.crawler_pdf_dir = Path(crawler_pdf_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.crawler_pdf_dir.mkdir(parents=True, exist_ok=True)

        self.parser = LegalDocumentParser()
        self.enricher = PeraturanMetadataEnricher()
        self.parsed_file = self.storage_dir / "parsed_regulations.json"

    def download_pdf(self, pdf_url: str, output_filename: Optional[str] = None) -> Optional[Path]:
        """Downloads a PDF file into the crawler pdf folder."""
        if not output_filename:
            output_filename = pdf_url.split("/")[-1].split("?")[0]
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"

        dest_path = self.crawler_pdf_dir / output_filename
        if dest_path.exists() and dest_path.stat().st_size > 1000:
            return dest_path

        try:
            req = urllib.request.Request(pdf_url, headers={"User-Agent": self.enricher.USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
                f.write(resp.read())
            return dest_path
        except Exception as e:
            return None

    def ingest_from_detail_url(self, detail_url: str) -> List[LegalArticle]:
        """Scrapes metadata, downloads PDF, parses articles, and appends to storage."""
        meta = self.enricher.scrape_regulation_detail(detail_url)
        if not meta or not meta.get("pdf_url"):
            return []

        pdf_path = self.download_pdf(meta["pdf_url"])
        if not pdf_path:
            return []

        # Parse PDF text
        raw_text = self.parser.extract_text_from_pdf(str(pdf_path))
        reg_status = (
            RegulationStatus.DICABUT_SELURUHNYA
            if "dicabut" in meta.get("status", "").lower()
            else RegulationStatus.BERLAKU
        )

        articles = self.parser.parse_text_to_articles(
            raw_text=raw_text,
            regulation_name=meta.get("title") or f"{meta.get('jenis')} No {meta.get('nomor')} Tahun {meta.get('tahun')}",
            regulation_number=f"{meta.get('jenis')} No. {meta.get('nomor')} Tahun {meta.get('tahun')}",
            regulation_year=meta.get("tahun") or 2024,
            hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
            status=reg_status
        )

        self.save_articles_to_storage(articles)

        # Persist directly into PostgreSQL (owlexia_db)
        try:
            from engine.database import OwlexiaDatabase
            db = OwlexiaDatabase()
            slug = f"{meta.get('jenis', 'uu')}-{meta.get('nomor', '0')}-{meta.get('tahun', '2024')}".lower().replace(" ", "-").replace(".", "")
            reg_id = db.upsert_regulation({
                "peraturan_id_slug": slug,
                "jenis": meta.get("jenis") or "Undang-Undang",
                "nomor": str(meta.get("nomor", "0")),
                "tahun": int(meta.get("tahun") or 2024),
                "judul": meta.get("title") or f"{meta.get('jenis')} No {meta.get('nomor')} Tahun {meta.get('tahun')}",
                "status": reg_status.value if hasattr(reg_status, 'value') else str(reg_status),
                "sumber_url": detail_url,
                "pdf_path": str(pdf_path),
                "total_pasal": len(articles),
                "metadata": {"crawled_at": str(os.path.getmtime(pdf_path))}
            })
            article_payloads = []
            for a in articles:
                article_payloads.append({
                    "article_number": a.article_number,
                    "chapter": a.chapter,
                    "part": a.notes,
                    "content": a.content,
                    "explanation": a.explanation,
                    "category": "pidana_materiil" if "kuhp" in slug else "umum",
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                    "keywords": [],
                    "metadata": {"notes": a.notes}
                })
            db.upsert_articles_batch(reg_id, article_payloads)
            db.log_crawler_job(
                source_url=detail_url,
                status="INDEXED",
                total_articles=len(articles),
                file_path=str(pdf_path)
            )
        except Exception as e:
            # Fallback continues if DB temporarily unavailable
            pass

        return articles

    def save_articles_to_storage(self, new_articles: List[LegalArticle]):
        """Persists parsed articles to json file."""
        existing_articles = self.load_stored_articles()
        existing_ids = {a.id for a in existing_articles}

        for art in new_articles:
            if art.id not in existing_ids:
                existing_articles.append(art)
                existing_ids.add(art.id)

        data = [a.model_dump() for a in existing_articles]
        with open(self.parsed_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_stored_articles(self) -> List[LegalArticle]:
        """Loads all stored parsed articles."""
        if not self.parsed_file.exists():
            return []
        try:
            with open(self.parsed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [LegalArticle(**item) for item in data]
        except Exception:
            return []
