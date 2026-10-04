"""Tests for Gemini LLM Integration and IRAC Legal Reasoning."""
import pytest
from engine.models import LegalArticle, FactCompleteness, LegalHierarchyLevel, RegulationStatus
from engine.reasoner import LegalReasoner
from engine.config import get_gemini_api_key, get_gemini_model


@pytest.fixture
def sample_article():
    return LegalArticle(
        id="test-art-1",
        regulation_name="Kitab Undang-Undang Hukum Pidana",
        regulation_number="WvS 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        article_number="340",
        content="Barang siapa sengaja dan dengan rencana lebih dahulu merampas nyawa orang lain, diancam, karena pembunuhan dengan rencana, dengan pidana mati atau pidana penjara seumur hidup atau selama waktu tertentu, paling lama dua puluh tahun."
    )


def test_gemini_fallback_on_invalid_key(sample_article):
    """Ensure LegalReasoner gracefully falls back to heuristic reasoning if API key is invalid."""
    reasoner = LegalReasoner(mode="llm", api_key="INVALID_TEST_KEY", model="gemini-3.5-flash")
    completeness = FactCompleteness(score=1.0)

    # Query matching family murder
    query = "apakah seseorang yang membunuh satu keluarga bisa didakwakan seumur hidup?"
    assessment = reasoner.analyze(query, [sample_article], completeness, force_mode="llm")

    # Should fall back cleanly without raising exception
    assert assessment is not None
    assert "SEUMUR HIDUP" in assessment.conclusion.upper()
    assert len(assessment.applicable_rules) > 0


def test_gemini_live_reasoning_if_configured(sample_article):
    """Test live Gemini reasoning if valid API key is present."""
    api_key = get_gemini_api_key()
    if not api_key:
        pytest.skip("No GEMINI_API_KEY configured for live test")

    reasoner = LegalReasoner(mode="llm", api_key=api_key, model=get_gemini_model())
    completeness = FactCompleteness(score=1.0)

    query = "Bagaimana ancaman hukuman bagi pelaku pembunuhan berencana?"
    assessment = reasoner.analyze(query, [sample_article], completeness, force_mode="llm")

    assert assessment is not None
    assert assessment.issue != ""
    assert assessment.application_analysis != ""
    assert assessment.conclusion != ""
    assert isinstance(assessment.aggravating_factors, list)
