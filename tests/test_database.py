"""Unit tests for Owlexia PostgreSQL Database adapter."""
import pytest
from engine.database import OwlexiaDatabase


def test_database_connection():
    db = OwlexiaDatabase()
    assert db.test_connection() is True


def test_database_count():
    db = OwlexiaDatabase()
    count = db.get_total_articles_count()
    assert count > 0


def test_database_regulations_list():
    db = OwlexiaDatabase()
    regs = db.get_regulations_list()
    assert len(regs) > 0
    slugs = [r["peraturan_id_slug"] for r in regs]
    assert any("kuhp" in s for s in slugs)


def test_database_fts_search():
    db = OwlexiaDatabase()
    results = db.search_articles_fts("pembunuhan", limit=5)
    assert len(results) > 0
    # Must retrieve Pasal 338 or 340 or 458
    articles = [r["article_number"] for r in results]
    assert any(num in ["338", "340", "458", "459"] for num in articles)
