"""Test suite untuk FastAPI endpoints Legal AI Agent."""
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_api_root():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_api_crawler_status():
    response = client.get("/api/crawler-status")
    assert response.status_code == 200
    data = response.json()
    assert data["crawler_found"] is True


def test_api_regulations_list():
    response = client.get("/api/regulations")
    assert response.status_code == 200
    data = response.json()
    assert data["total_articles"] > 0


def test_api_query_clarification_mode():
    payload = {"query": "apa hukuman bagi seorang yang membunuh kedua orang tuanya"}
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_clarification_mode"] is True
    assert len(data["clarification_questions"]) > 0


def test_api_query_with_context():
    payload = {
        "query": "apa hukuman bagi seorang yang membunuh kedua orang tuanya",
        "case_context": {"direncanakan": True, "rezim_kuhp": "KUHP_LAMA_WVS"},
        "force_assessment": True
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_clarification_mode"] is False
    assert data["assessment"] is not None
    assert "SEUMUR HIDUP" in data["assessment"]["conclusion"].upper() or "PIDANA MATI" in data["assessment"]["conclusion"].upper()


def test_api_query_database_metadata():
    payload = {"query": "apa saja peraturan yang ada di database kamu"}
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_clarification_mode"] is False
    assert data["assessment"] is None
    assert "OWLEXIA" in data["message"]
    assert "KUHP" in data["message"]


def test_api_query_greeting():
    payload = {"query": "Halo, siapa kamu?"}
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_clarification_mode"] is False
    assert data["assessment"] is None
    assert "OWLEXIA" in data["message"]

