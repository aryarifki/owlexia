"""Metadata Enricher & Scraper untuk peraturan.go.id.

Mengambil informasi detail regulasi (Status Keberlakuan, Nomor, Tahun, Judul, URL PDF)
dari halaman web resmi peraturan.go.id.
"""
import urllib.request
import urllib.parse
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup


class PeraturanMetadataEnricher:
    """Scrapes structured metadata from peraturan.go.id detail pages."""

    BASE_URL = "https://peraturan.go.id"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def fetch_page_html(self, url: str) -> Optional[str]:
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return None

    def scrape_regulation_detail(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrapes a regulation detail page, returning rich metadata dict.
        """
        if not detail_url.startswith("http"):
            detail_url = urllib.parse.urljoin(self.BASE_URL, detail_url)

        html = self.fetch_page_html(detail_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        metadata: Dict[str, Any] = {
            "detail_url": detail_url,
            "title": "",
            "jenis": "",
            "nomor": "",
            "tahun": 0,
            "tentang": "",
            "status": "Berlaku",
            "pdf_url": "",
            "tanggal_pengundangan": ""
        }

        # Title
        h1 = soup.find("h1")
        if h1:
            metadata["title"] = h1.get_text(strip=True)

        # Cari data dari tabel-tabel detail
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if len(cols) >= 2:
                    key = cols[0].lower()
                    val = cols[1]
                    if "jenis" in key or "bentuk" in key:
                        metadata["jenis"] = val
                    elif "nomor" == key:
                        metadata["nomor"] = val
                    elif "tahun" == key:
                        try:
                            metadata["tahun"] = int(re.sub(r"[^\d]", "", val))
                        except ValueError:
                            pass
                    elif "tentang" in key:
                        metadata["tentang"] = val
                    elif "status" in key:
                        metadata["status"] = val
                    elif "tanggal pengundangan" in key:
                        metadata["tanggal_pengundangan"] = val

        # Status ekstraksi dari text badge jika tabel tidak memuatnya
        text_lower = soup.get_text().lower()
        if "statusberlaku" in text_lower or "status: berlaku" in text_lower or "status berlaku" in text_lower:
            metadata["status"] = "Berlaku"
        elif "dicabut" in text_lower:
            metadata["status"] = "Dicabut"

        # Temukan link file PDF
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf") or "/files/" in href:
                metadata["pdf_url"] = urllib.parse.urljoin(self.BASE_URL, href)
                break

        return metadata
