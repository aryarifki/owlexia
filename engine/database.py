"""PostgreSQL Database Adapter for OWLEXIA Legal AI Agent.

Handles connection pooling, upserts of crawled regulations, hierarchical articles,
Indonesian full-text search (tsvector/GIN), and crawler monitoring logs.
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json

from engine.models import LegalArticle, LegalHierarchyLevel, RegulationStatus

logger = logging.getLogger("owlexia.database")

DEFAULT_DB_URL = "postgresql://owlexia:owlexia_pass@localhost:5432/owlexia_db"


class OwlexiaDatabase:
    """Enterprise PostgreSQL manager for OWLEXIA."""

    @staticmethod
    def map_jenis_to_hierarchy(jenis_str: Optional[str]) -> LegalHierarchyLevel:
        """Maps Indonesian regulation type string to LegalHierarchyLevel enum."""
        j = (jenis_str or "").lower()
        if "uud" in j:
            return LegalHierarchyLevel.UUD1945
        elif "mpr" in j or "tap" in j:
            return LegalHierarchyLevel.TAP_MPR
        elif "perpres" in j or "presiden" in j:
            return LegalHierarchyLevel.PERPRES
        elif "pemerintah pengganti" in j or "perppu" in j or "perpu" in j:
            return LegalHierarchyLevel.UU_PERPPU
        elif "pemerintah" in j or j == "pp":
            return LegalHierarchyLevel.PP
        elif "menteri" in j or "permen" in j:
            return LegalHierarchyLevel.PERMEN
        elif "mk" in j or "konstitusi" in j:
            return LegalHierarchyLevel.PUTUSAN_MK
        elif "ma" in j or "agung" in j or "yurisprudensi" in j:
            return LegalHierarchyLevel.YURISPRUDENSI_MA
        else:
            return LegalHierarchyLevel.UU_PERPPU

    def _row_to_model(self, r: Dict[str, Any]) -> LegalArticle:
        """Converts PostgreSQL database row dictionary to LegalArticle model."""
        reg_status_str = str(r.get("regulation_status") or r.get("article_status") or "BERLAKU").upper()
        try:
            status = RegulationStatus(reg_status_str)
        except Exception:
            status = RegulationStatus.BERLAKU

        return LegalArticle(
            id=str(r.get("id")),
            regulation_name=r.get("regulation_name") or r.get("jenis") or "Regulasi",
            regulation_number=str(r.get("nomor", "0")),
            regulation_year=int(r.get("tahun") or 2024),
            hierarchy_level=self.map_jenis_to_hierarchy(r.get("jenis")),
            status=status,
            chapter=r.get("chapter"),
            part=r.get("part"),
            article_number=str(r.get("article_number", "0")),
            content=r.get("content", ""),
            explanation=r.get("explanation"),
            effective_date=None,
            notes=None,
        )

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

    def get_all_articles_as_models(self) -> List[LegalArticle]:
        """Loads all articles from PostgreSQL into structured LegalArticle models."""
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
            r.status as regulation_status
        FROM legal_articles a
        JOIN regulations r ON a.regulation_id = r.id
        ORDER BY r.tahun DESC, r.nomor, a.id;
        """
        articles = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql)
                    for r in cur.fetchall():
                        articles.append(self._row_to_model(dict(r)))
        except Exception as e:
            logger.error(f"Error loading articles as models: {e}")
        return articles

    def search_articles_fts(self, query_str: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs full-text search with ranking and trigram similarity across all regulations."""
        tokens = [re.sub(r"[^\w]", "", w.lower()) for w in query_str.split()]
        tokens = [t for t in tokens if len(t) >= 2]
        or_query = " | ".join(tokens) if tokens else query_str

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
            (
                COALESCE(ts_rank_cd(a.tsv_content, plainto_tsquery('indonesian', %(query)s)), 0.0) * 3.0 +
                COALESCE(ts_rank_cd(a.tsv_content, to_tsquery('indonesian', %(or_query)s)), 0.0) * 1.0 +
                COALESCE(similarity(a.content, %(query)s), 0.0) * 2.0
            ) as rank_score,
            similarity(a.content, %(query)s) as sim_score
        FROM legal_articles a
        JOIN regulations r ON a.regulation_id = r.id
        WHERE 
            a.tsv_content @@ plainto_tsquery('indonesian', %(query)s)
            OR (%(or_query)s <> '' AND a.tsv_content @@ to_tsquery('indonesian', %(or_query)s))
            OR a.content ILIKE %(like_query)s
            OR r.judul ILIKE %(like_query)s
            OR a.article_number = %(clean_num)s
        ORDER BY rank_score DESC, sim_score DESC
        LIMIT %(limit)s;
        """
        results = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, {
                        "query": query_str,
                        "or_query": or_query,
                        "like_query": f"%{query_str}%",
                        "clean_num": query_str.strip(),
                        "limit": limit
                    })
                    rows = cur.fetchall()
                    for r in rows:
                        results.append(dict(r))
        except Exception as e:
            # Fallback to simple query if to_tsquery syntax errors on special characters
            logger.warning(f"FTS enhanced query error, falling back to simple plainto_tsquery: {e}")
            simple_sql = """
            SELECT 
                a.id, a.article_number, a.chapter, a.part, a.content, a.explanation,
                a.status as article_status, r.peraturan_id_slug, r.jenis, r.nomor, r.tahun,
                r.judul as regulation_name, r.status as regulation_status,
                ts_rank_cd(a.tsv_content, plainto_tsquery('indonesian', %(query)s)) as rank_score,
                similarity(a.content, %(query)s) as sim_score
            FROM legal_articles a
            JOIN regulations r ON a.regulation_id = r.id
            WHERE a.tsv_content @@ plainto_tsquery('indonesian', %(query)s)
               OR a.content ILIKE %(like_query)s
            ORDER BY rank_score DESC, sim_score DESC
            LIMIT %(limit)s;
            """
            try:
                with self.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(simple_sql, {
                            "query": query_str,
                            "like_query": f"%{query_str}%",
                            "limit": limit
                        })
                        for r in cur.fetchall():
                            results.append(dict(r))
            except Exception as e2:
                logger.error(f"FTS fallback search error: {e2}")
        return results

    def search_articles_as_models(self, query_str: str, limit: int = 5) -> List[LegalArticle]:
        """Returns search results as LegalArticle model instances."""
        rows = self.search_articles_fts(query_str, limit=limit)
        return [self._row_to_model(r) for r in rows]

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
