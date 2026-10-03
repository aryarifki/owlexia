"""Test suite untuk Indonesian Legal AI Agent."""
import pytest
from engine.models import RegulationStatus
from engine.retriever import LegalRetriever
from engine.proactive_agent import ProactiveCaseAnalyzer
from engine.reasoner import LegalReasoner
from engine.agent_system import LegalAgentOrchestrator
from seed_regulations import get_all_articles
from crawler_connector.connector import CrawlerConnector


@pytest.fixture
def articles():
    return get_all_articles()


@pytest.fixture
def retriever(articles):
    return LegalRetriever(articles)


@pytest.fixture
def analyzer():
    return ProactiveCaseAnalyzer()


@pytest.fixture
def reasoner():
    return LegalReasoner()


@pytest.fixture
def orchestrator():
    return LegalAgentOrchestrator()


def test_retriever_indexing_and_search(retriever):
    """Test BM25 + Semantic Hybrid Search."""
    results = retriever.search("pembunuhan berencana", top_k=3)
    assert len(results) > 0
    top_article, score = results[0]
    # Harusnya menemukan Pasal 340 KUHP atau Pasal 459 UU 1/2023
    assert top_article.article_number in ["340", "459"]


def test_retriever_suspect_mk_boost(retriever):
    """Test retrieval for suspect determination finding MK ruling."""
    results = retriever.search("bagaimana alur polisi menetapkan status tersangka", top_k=3)
    assert len(results) > 0
    article_numbers = [art.article_number for art, _ in results]
    # Harus menyertakan norma penetapan tersangka atau Putusan MK
    assert any("21/PUU-XII/2014" in num or "1 angka 14" in num or "184" in num for num in article_numbers)


def test_proactive_agent_clarification_trigger(analyzer):
    """Test proactive agent triggers clarification on vague murder question."""
    completeness = analyzer.evaluate_facts("apa hukuman bagi seorang yang membunuh kedua orang tuanya")
    assert completeness.needs_clarification is True
    assert "unsur_perencanaan" in completeness.missing_critical_elements
    assert completeness.score < 0.85

    questions = analyzer.generate_clarification_questions("apa hukuman bagi seorang yang membunuh kedua orang tuanya", completeness)
    assert len(questions) >= 1
    assert any(q.id == "q_perencanaan" for q in questions)


def test_proactive_agent_suspect_clarification(analyzer):
    """Test proactive agent on suspect procedure."""
    completeness = analyzer.evaluate_facts("bagaimana polisi menetapkan status tersangka")
    assert completeness.needs_clarification is True
    assert "kecukupan_alat_bukti" in completeness.missing_critical_elements or "pemeriksaan_calon_tersangka" in completeness.missing_critical_elements

    questions = analyzer.generate_clarification_questions("bagaimana polisi menetapkan status tersangka", completeness)
    assert len(questions) >= 1
    assert any(q.id == "q_prosedur_tersangka" for q in questions)


def test_reasoner_family_murder_life_imprisonment(reasoner, retriever, analyzer):
    """Test legal reasoning on family murder and life imprisonment."""
    query = "apakah seseorang yang membunuh satu keluarga bisa didakwakan/ dihukum seumur hidup?"
    completeness = analyzer.evaluate_facts(query)
    results = retriever.search(query, top_k=5)
    articles = [a for a, _ in results]

    assessment = reasoner.analyze(query, articles, completeness)
    assert "SEUMUR HIDUP" in assessment.conclusion.upper()
    assert len(assessment.applicable_rules) > 0


def test_reasoner_suspect_procedure_mk21(reasoner, retriever, analyzer):
    """Test legal reasoning on suspect status includes MK 21/PUU-XII/2014."""
    query = "bagaimana alur polisi menetapkan status tersangka"
    completeness = analyzer.evaluate_facts(query)
    results = retriever.search(query, top_k=5)
    articles = [a for a, _ in results]

    assessment = reasoner.analyze(query, articles, completeness)
    assert "21/PUU-XII/2014" in assessment.application_analysis
    assert len(assessment.procedural_steps) >= 5


def test_orchestrator_two_phase_flow(orchestrator):
    """Test orchestrator flow: phase 1 clarification, phase 2 full assessment."""
    query = "apa hukuman bagi seorang yang membunuh kedua orang tuanya"
    
    # Round 1: Expect clarification mode
    resp1 = orchestrator.process_query(query)
    assert resp1.is_clarification_mode is True
    assert len(resp1.questions) > 0

    # Round 2: Provide facts from user, expect final assessment
    user_answers = {"direncanakan": True, "rezim_kuhp": "KUHP_LAMA_WVS"}
    resp2 = orchestrator.process_query(query, case_context=user_answers, force_assessment=True)
    assert resp2.is_clarification_mode is False
    assert resp2.assessment is not None
    assert "PIDANA MATI" in resp2.assessment.conclusion.upper() or "SEUMUR HIDUP" in resp2.assessment.conclusion.upper()


def test_crawler_connector():
    """Test crawler connector detects existing Peraturan-Crawler repository."""
    connector = CrawlerConnector("/root/Peraturan-Crawler")
    assert connector.is_crawler_available() is True
    stats = connector.get_crawler_stats()
    assert stats["crawler_found"] is True
