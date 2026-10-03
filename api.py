"""FastAPI Backend Server for Indonesian Legal AI Agent."""
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.agent_system import LegalAgentOrchestrator
from engine.database import OwlexiaDatabase
from crawler_connector.connector import CrawlerConnector
from crawler_connector.pipeline import LegalDataPipeline
from seed_regulations import get_all_articles

app = FastAPI(
    title="OWLEXIA API - Indonesian Legal AI Intelligence",
    description="Sistem Intelijen & Penalaran Hukum Proaktif Indonesia berbasis Peraturan.go.id, KUHP WvS, UU 1/2023, KUHAP, dan Yurisprudensi MK",
    version="1.0.0"
)

from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from engine.prompt_manager import PromptManager

orchestrator = LegalAgentOrchestrator()
connector = CrawlerConnector()
pipeline = LegalDataPipeline()
db = OwlexiaDatabase()
prompt_manager = PromptManager()


class QueryRequest(BaseModel):
    query: str
    case_context: Optional[Dict[str, Any]] = None
    force_assessment: bool = False


class IngestRequest(BaseModel):
    detail_url: str


class UpdatePromptRequest(BaseModel):
    prompt_content: str


@app.get("/api/prompt")
def get_system_prompt():
    return {
        "metadata": prompt_manager.get_metadata(),
        "prompt_content": prompt_manager.get_system_prompt()
    }


@app.post("/api/prompt")
def update_system_prompt(req: UpdatePromptRequest):
    if not req.prompt_content.strip():
        raise HTTPException(status_code=400, detail="Prompt content cannot be empty")
    success = prompt_manager.update_system_prompt(req.prompt_content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save prompt file")
    return {
        "success": True,
        "message": "System prompt updated and hot-reloaded successfully",
        "metadata": prompt_manager.get_metadata()
    }


@app.get("/api/health")
def health():
    db_ok = db.test_connection()
    return {
        "status": "online",
        "service": "OWLEXIA - Indonesian Legal AI Intelligence",
        "version": "1.0.0",
        "database": "connected" if db_ok else "offline",
        "db_articles_count": db.get_total_articles_count() if db_ok else 0
    }


@app.get("/api/crawler-status")
def get_crawler_status():
    stats = connector.get_crawler_stats()
    stats["db_connected"] = db.test_connection()
    stats["db_regulations"] = db.get_regulations_list()
    return stats


@app.get("/api/regulations")
def list_regulations():
    articles = orchestrator.retriever.articles
    return {
        "total_articles": len(articles),
        "articles": [
            {
                "id": a.id,
                "regulation": a.regulation_name,
                "number": a.regulation_number,
                "article": a.article_number,
                "status": a.status.value,
                "chapter": a.chapter
            }
            for a in articles
        ]
    }


@app.post("/api/query")
def process_legal_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    resp = orchestrator.process_query(
        user_query=req.query,
        case_context=req.case_context,
        force_assessment=req.force_assessment
    )

    return {
        "is_clarification_mode": resp.is_clarification_mode,
        "message": resp.message,
        "completeness_score": resp.completeness.score,
        "missing_elements": resp.completeness.missing_critical_elements,
        "clarification_questions": [q.model_dump() for q in resp.questions],
        "assessment": resp.assessment.model_dump() if resp.assessment else None,
        "retrieved_articles": [a.model_dump() for a in resp.retrieved_articles]
    }


@app.post("/api/ingest")
def ingest_regulation(req: IngestRequest):
    if not req.detail_url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    try:
        articles = pipeline.ingest_from_detail_url(req.detail_url)
        if not articles:
            raise HTTPException(status_code=422, detail="Failed to scrape or extract articles from URL")
        orchestrator.retriever.add_articles(articles)
        return {
            "success": True,
            "regulation_name": articles[0].regulation_name,
            "regulation_number": articles[0].regulation_number,
            "articles_extracted": len(articles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount compiled React/Vite web application for direct fullstack serving
web_dist = Path(__file__).resolve().parent / "web" / "dist"
static_dir = Path(__file__).resolve().parent / "static"

if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web_dist")
elif static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
