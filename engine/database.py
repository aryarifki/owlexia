"""PostgreSQL Database Adapter for OWLEXIA Legal AI Agent.

Handles connection pooling, upserts of crawled regulations, hierarchical articles,
Indonesian full-text search (tsvector/GIN), and crawler monitoring logs.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger("owlexia.database")

DEFAULT_DB_URL = "postgresql://owlexia:owlexia_pass@localhost:5432/owlexia_db"


class OwlexiaDatabase:
    """Enterprise PostgreSQL manager for OWLEXIA."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", DEFAULT_DB_URL)

    def get_connection(self):
        """Returns a psycopg2 database connection."""
        return psycopg2.connect(self.db_url)

    def test_connection(self) -> bool:
        """Verifies database availability."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return cur.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False

    def upsert_regulation(self, reg_data: Dict[str, Any]) -> str:
        """Inserts or updates a regulation record and returns its UUID."""
        query = """
        INSERT INTO regulations (
            peraturan_id_slug, jenis, nomor, tahun, judul, status,
            tanggal_pengundangan, sumber_url, pdf_path, total_pasal, metadata
        ) VALUES (
            %(slug)s, %(jenis)s, %(nomor)s, %(tahun)s, %(judul)s, %(status)s,
            %(tanggal_pengundangan)s, %(sumber_url)s, %(pdf_path)s, %(total_pasal)s, %(metadata)s
        )
        ON CONFLICT (peraturan_id_slug) DO UPDATE SET
            judul = EXCLUDED.judul,
            status = EXCLUDED.status,
            sumber_url = COALESCE(EXCLUDED.sumber_url, regulations.sumber_url),
            pdf_path = COALESCE(EXCLUDED.pdf_path, regulations.pdf_path),
            total_pasal = GREATEST(regulations.total_pasal, EXCLUDED.total_pasal),
            metadata = regulations.metadata || EXCLUDED.metadata,
            updated_at = NOW()
        RETURNING id;
        """
        slug = reg_data.get("peraturan_id_slug") or f"{reg_data.get('jenis','uu')}-{reg_data.get('nomor','0')}-{reg_data.get('tahun','2024')}".lower().replace(" ", "-")
        params = {
            "slug": slug,
            "jenis": reg_data.get("jenis", "Undang-Undang"),
            "nomor": str(reg_data.get("nomor", "0")),
            "tahun": int(reg_data.get("tahun", 2024)),
            "judul": reg_data.get("judul", ""),
            "status": reg_data.get("status", "BERLAKU"),
            "tanggal_pengundangan": reg_data.get("tanggal_pengundangan"),
            "sumber_url": reg_data.get("sumber_url"),
            "pdf_path": reg_data.get("pdf_path"),
            "total_pasal": int(reg_data.get("total_pasal", 0)),
            "metadata": Json(reg_data.get("metadata", {}))
        }

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                res = cur.fetchone()
                conn.commit()
                return str(res[0])

    def upsert_article(self, regulation_id: str, article: Dict[str, Any]) -> str:
        """Upserts a single legal article linked to a regulation."""
        query = """
        INSERT INTO legal_articles (
            regulation_id, article_number, chapter, part,
            content, explanation, category, status, keywords, metadata
        ) VALUES (
            %(reg_id)s, %(article_number)s, %(chapter)s, %(part)s,
            %(content)s, %(explanation)s, %(category)s, %(status)s, %(keywords)s, %(metadata)s
        )
        ON CONFLICT (regulation_id, article_number) DO UPDATE SET
            chapter = COALESCE(EXCLUDED.chapter, legal_articles.chapter),
            part = COALESCE(EXCLUDED.part, legal_articles.part),
            content = EXCLUDED.content,
            explanation = COALESCE(EXCLUDED.explanation, legal_articles.explanation),
            category = COALESCE(EXCLUDED.category, legal_articles.category),
            status = EXCLUDED.status,
            keywords = EXCLUDED.keywords,
            metadata = legal_articles.metadata || EXCLUDED.metadata,
            updated_at = NOW()
        RETURNING id;
        """
        params = {
            "reg_id": regulation_id,
            "article_number": str(article.get("article_number", "0")),
            "chapter": article.get("chapter"),
            "part": article.get("part"),
            "content": article.get("content", ""),
            "explanation": article.get("explanation"),
            "category": article.get("category", "pidana_materiil"),
            "status": article.get("status", "BERLAKU"),
            "keywords": article.get("keywords", []),
            "metadata": Json(article.get("metadata", {}))
        }

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                res = cur.fetchone()
                conn.commit()
                return str(res[0])

    def upsert_articles_batch(self, regulation_id: str, articles: List[Dict[str, Any]]) -> int:
        """Efficiently batch-inserts multiple articles for a regulation."""
        if not articles:
            return 0
        count = 0
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for art in articles:
                    cur.execute("""
                    INSERT INTO legal_articles (
                        regulation_id, article_number, chapter, part,
                        content, explanation, category, status, keywords, metadata
                    ) VALUES (
                        %(reg_id)s, %(article_number)s, %(chapter)s, %(part)s,
                        %(content)s, %(explanation)s, %(category)s, %(status)s, %(keywords)s, %(metadata)s
                    )
                    ON CONFLICT (regulation_id, article_number) DO UPDATE SET
                        content = EXCLUDED.content,
                        explanation = COALESCE(EXCLUDED.explanation, legal_articles.explanation),
                        status = EXCLUDED.status,
                        updated_at = NOW();
                    """, {
                        "reg_id": regulation_id,
                        "article_number": str(art.get("article_number", "0")),
                        "chapter": art.get("chapter"),
                        "part": art.get("part"),
                        "content": art.get("content", ""),
                        "explanation": art.get("explanation"),
                        "category": art.get("category", "pidana_materiil"),
                        "status": art.get("status", "BERLAKU"),
                        "keywords": art.get("keywords", []),
                        "metadata": Json(art.get("metadata", {}))
                    })
                    count += 1
                # Update total_pasal on regulation
                cur.execute("""
                    UPDATE regulations SET total_pasal = (
                        SELECT COUNT(*) FROM legal_articles WHERE regulation_id = %s
                    ) WHERE id = %s;
                """, (regulation_id, regulation_id))
                conn.commit()
        return count

    def search_articles_fts(self, query_str: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs full-text search with ranking and trigram similarity."""
        sql = """
        SELECT 
            a.id,
            a.article_number,
            a.chapter,
            a.part,
            a.content,
            a.explanation,
            a.status as article_status,
            r.peraturan_id_slug,
            r.jenis,
            r.nomor,
            r.tahun,
            r.judul as regulation_name,
            r.status as regulation_status,
            ts_rank_cd(a.tsv_content, plainto_tsquery('indonesian', %(query)s)) as rank_score,
            similarity(a.content, %(query)s) as sim_score
        FROM legal_articles a
        JOIN regulations r ON a.regulation_id = r.id
        WHERE 
            a.tsv_content @@ plainto_tsquery('indonesian', %(query)s)
            OR a.content ILIKE %(like_query)s
        ORDER BY rank_score DESC, sim_score DESC
        LIMIT %(limit)s;
        """
        results = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, {
                        "query": query_str,
                        "like_query": f"%{query_str}%",
                        "limit": limit
                    })
                    rows = cur.fetchall()
                    for r in rows:
                        results.append(dict(r))
        except Exception as e:
            logger.error(f"FTS search error: {e}")
        return results

    def get_total_articles_count(self) -> int:
        """Returns total active legal articles in PostgreSQL."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM legal_articles;")
                    row = cur.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"Count query error: {e}")
            return 0

    def get_regulations_list(self) -> List[Dict[str, Any]]:
        """Returns list of indexed regulations."""
        sql = """
        SELECT id, peraturan_id_slug, jenis, nomor, tahun, judul, status, total_pasal, updated_at
        FROM regulations
        ORDER BY tahun DESC, nomor DESC;
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql)
                    return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"Get regulations error: {e}")
            return []

    def log_crawler_job(self, source_url: str, status: str, total_articles: int = 0, file_path: Optional[str] = None, error_message: Optional[str] = None):
        """Records crawling execution job history."""
        sql = """
        INSERT INTO crawler_jobs (source_url, status, total_articles, file_path, error_message, completed_at)
        VALUES (%(url)s, %(status)s, %(total)s, %(file_path)s, %(err)s, CASE WHEN %(status)s IN ('INDEXED', 'FAILED') THEN NOW() ELSE NULL END);
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, {
                        "url": source_url,
                        "status": status,
                        "total": total_articles,
                        "file_path": file_path,
                        "err": error_message
                    })
                    conn.commit()
        except Exception as e:
            logger.error(f"Crawler job log error: {e}")
