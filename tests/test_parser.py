"""Unit test untuk LegalDocumentParser dan Data Pipeline."""
import pytest
from engine.parser import LegalDocumentParser
from engine.models import LegalHierarchyLevel, RegulationStatus
from crawler_connector.pipeline import LegalDataPipeline


SAMPLE_LAW_TEXT = """
UNDANG-UNDANG REPUBLIK INDONESIA
NOMOR 99 TAHUN 2024
TENTANG
PENEGAKAN HUKUM DAN KEADILAN

DENGAN RAHMAT TUHAN YANG MAHA ESA
PRESIDEN REPUBLIK INDONESIA,

BAB I
KETENTUAN UMUM

Pasal 1
(1) Penegakan hukum diselenggarakan berdasarkan prinsip keadilan dan transparansi.
(2) Setiap aparatur penegak hukum wajib menjunjung tinggi hak asasi manusia.

Pasal 2
Setiap orang berhak atas bantuan hukum yang layak sejak saat penangkapan atau penetapan status tersangka.

BAB II
SANKSI PIDANA

Pasal 3
Barang siapa dengan sengaja menghalang-halangi proses peradilan diancam dengan pidana penjara paling lama 5 tahun.

PENJELASAN ATAS
UNDANG-UNDANG REPUBLIK INDONESIA NOMOR 99 TAHUN 2024
TENTANG PENEGAKAN HUKUM DAN KEADILAN

I. UMUM
...

II. PASAL DEMI PASAL

Pasal 1
Cukup jelas.

Pasal 2
Yang dimaksud dengan "sejak saat penangkapan" adalah terhitung seketika saat tindakan fisik penahanan atau pembatasan kebebasan dilakukan.

Pasal 3
Ketentuan ini mengatur delik obstruction of justice.
"""


def test_parse_law_text_hierarchical():
    parser = LegalDocumentParser()
    articles = parser.parse_text_to_articles(
        raw_text=SAMPLE_LAW_TEXT,
        regulation_name="UU Penegakan Hukum",
        regulation_number="UU No. 99 Tahun 2024",
        regulation_year=2024
    )

    assert len(articles) == 3

    # Check Pasal 1
    art1 = next(a for a in articles if a.article_number == "1")
    assert "BAB I" in art1.chapter
    assert "prinsip keadilan" in art1.content
    assert art1.explanation == "Cukup jelas."

    # Check Pasal 2
    art2 = next(a for a in articles if a.article_number == "2")
    assert "bantuan hukum" in art2.content
    assert "Yang dimaksud dengan \"sejak saat penangkapan\"" in art2.explanation

    # Check Pasal 3
    art3 = next(a for a in articles if a.article_number == "3")
    assert "BAB II" in art3.chapter
    assert "obstruction of justice" in art3.explanation


def test_pipeline_storage(tmp_path):
    pipeline = LegalDataPipeline(
        storage_dir=str(tmp_path / "data"),
        crawler_pdf_dir=str(tmp_path / "pdf")
    )
    parser = LegalDocumentParser()
    articles = parser.parse_text_to_articles(
        raw_text=SAMPLE_LAW_TEXT,
        regulation_name="UU Penegakan Hukum",
        regulation_number="UU No. 99 Tahun 2024",
        regulation_year=2024
    )

    pipeline.save_articles_to_storage(articles)
    loaded = pipeline.load_stored_articles()
    assert len(loaded) == 3
    assert loaded[0].article_number == "1"
