"""Hierarchical Legal Document & PDF Parser for Indonesian Legislation.

Sesuai format baku UU No. 12 Tahun 2011 tentang Pembentukan Peraturan Perundang-undangan:
- Memecah dokumen hukum berdasarkan hierarki resmi:
  BAB -> Bagian -> Paragraf -> Pasal -> Ayat -> Penjelasan Pasal
- Menghindari pemotongan acak berbasis token sehingga substansi hukum per-pasal tetap utuh.
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from engine.models import LegalArticle, LegalHierarchyLevel, RegulationStatus

try:
    import pypdf
except ImportError:
    pypdf = None


class ParsedSection(BaseModel):
    article_number: str
    chapter: Optional[str] = None
    part: Optional[str] = None
    content: str
    explanation: Optional[str] = None


class LegalDocumentParser:
    """Parser untuk teks hukum perundang-undangan Indonesia."""

    # Regex untuk mendeteksi penanda hierarki hukum
    RE_BAB = re.compile(r"^\s*BAB\s+([IVXLCDM]+)\s*$", re.IGNORECASE | re.MULTILINE)
    RE_PASAL = re.compile(r"^\s*Pasal\s+(\d+[a-zA-Z]?)\s*$", re.IGNORECASE | re.MULTILINE)
    RE_PENJELASAN = re.compile(r"PENJELASAN\s+ATAS", re.IGNORECASE)
    RE_PASAL_DEMI_PASAL = re.compile(r"PASAL\s+DEMI\s+PASAL", re.IGNORECASE)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file using pypdf."""
        if not pypdf:
            raise ImportError("Library 'pypdf' belum terpasang. Jalankan pip install pypdf")

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file tidak ditemukan: {pdf_path}")

        reader = pypdf.PdfReader(str(path))
        full_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text.append(t)
        return "\n".join(full_text)

    def parse_text_to_articles(
        self,
        raw_text: str,
        regulation_name: str,
        regulation_number: str,
        regulation_year: int,
        hierarchy_level: LegalHierarchyLevel = LegalHierarchyLevel.UU_PERPPU,
        status: RegulationStatus = RegulationStatus.BERLAKU
    ) -> List[LegalArticle]:
        """
        Mem-parsing teks undang-undang lengkap menjadi daftar LegalArticle terstruktur.
        """
        # Pisahkan antara Tubuh Utama Undang-Undang dan Penjelasan
        main_body = raw_text
        explanation_body = ""

        penjelasan_match = self.RE_PENJELASAN.search(raw_text)
        if penjelasan_match:
            main_body = raw_text[:penjelasan_match.start()]
            explanation_body = raw_text[penjelasan_match.start():]

        # Ekstrak penjelasan per-pasal jika ada
        explanations_dict = self._extract_explanations(explanation_body)

        # Parsing pasal-pasal dari Tubuh Utama
        parsed_articles = []
        lines = main_body.splitlines()

        current_bab = None
        current_pasal = None
        current_content_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Deteksi BAB
            if line.upper().startswith("BAB "):
                # Ambil judul bab dari baris ini atau baris berikutnya
                current_bab = line
                if i + 1 < len(lines) and lines[i+1].isupper() and not lines[i+1].startswith("Pasal"):
                    current_bab += ": " + lines[i+1].strip()
                    i += 1
                i += 1
                continue

            # Deteksi Pasal
            pasal_match = re.match(r"^Pasal\s+(\d+[a-zA-Z]?)\s*$", line, re.IGNORECASE)
            if pasal_match:
                # Simpan pasal sebelumnya jika ada
                if current_pasal and current_content_lines:
                    content_str = "\n".join(current_content_lines).strip()
                    parsed_articles.append(
                        self._create_article_model(
                            article_num=current_pasal,
                            chapter=current_bab,
                            content=content_str,
                            explanation=explanations_dict.get(current_pasal),
                            reg_name=regulation_name,
                            reg_num=regulation_number,
                            reg_year=regulation_year,
                            hierarchy=hierarchy_level,
                            status=status
                        )
                    )
                    current_content_lines = []

                current_pasal = pasal_match.group(1)
                i += 1
                continue

            # Kumpulkan isi teks pasal
            if current_pasal:
                # Hindari baris footer nomor halaman atau disclaimer
                if not re.match(r"^\s*-\s*\d+\s*-\s*$", line) and not "www.peraturan.go.id" in line.lower():
                    current_content_lines.append(line)

            i += 1

        # Simpan pasal terakhir
        if current_pasal and current_content_lines:
            content_str = "\n".join(current_content_lines).strip()
            parsed_articles.append(
                self._create_article_model(
                    article_num=current_pasal,
                    chapter=current_bab,
                    content=content_str,
                    explanation=explanations_dict.get(current_pasal),
                    reg_name=regulation_name,
                    reg_num=regulation_number,
                    reg_year=regulation_year,
                    hierarchy=hierarchy_level,
                    status=status
                )
            )

        return parsed_articles

    def _extract_explanations(self, explanation_text: str) -> Dict[str, str]:
        """Ekstrak bagian PASAL DEMI PASAL dari dokumen penjelasan."""
        explanations = {}
        if not explanation_text:
            return explanations

        pdp_match = self.RE_PASAL_DEMI_PASAL.search(explanation_text)
        if not pdp_match:
            return explanations

        pdp_text = explanation_text[pdp_match.end():]
        lines = pdp_text.splitlines()

        current_pasal = None
        current_exp_lines = []

        for line in lines:
            line_str = line.strip()
            match = re.match(r"^Pasal\s+(\d+[a-zA-Z]?)\s*$", line_str, re.IGNORECASE)
            if match:
                if current_pasal and current_exp_lines:
                    explanations[current_pasal] = " ".join(current_exp_lines).strip()
                    current_exp_lines = []
                current_pasal = match.group(1)
                continue

            if current_pasal and line_str:
                if not re.match(r"^\s*-\s*\d+\s*-\s*$", line_str):
                    current_exp_lines.append(line_str)

        if current_pasal and current_exp_lines:
            explanations[current_pasal] = " ".join(current_exp_lines).strip()

        return explanations

    def _create_article_model(
        self,
        article_num: str,
        chapter: Optional[str],
        content: str,
        explanation: Optional[str],
        reg_name: str,
        reg_num: str,
        reg_year: int,
        hierarchy: LegalHierarchyLevel,
        status: RegulationStatus
    ) -> LegalArticle:
        safe_name = re.sub(r"[^\w]", "-", reg_name.lower())
        safe_num = re.sub(r"[^\w]", "-", str(article_num).lower())
        article_id = f"{safe_name}-{reg_year}-pasal-{safe_num}"

        return LegalArticle(
            id=article_id,
            regulation_name=reg_name,
            regulation_number=reg_num,
            regulation_year=reg_year,
            hierarchy_level=hierarchy,
            status=status,
            chapter=chapter,
            article_number=article_num,
            content=content,
            explanation=explanation
        )
