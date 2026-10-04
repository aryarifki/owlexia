"""Hybrid Legal Retrieval Engine (BM25 + Semantic Cosine + Metadata Filter).

Sesuai metodologi RAG Architect:
- Menggabungkan BM25 Okapi untuk pencarian pasal presisi (nomor pasal, istilah delik)
- Semantic Vectorizer (TF-IDF weighted cosine) untuk pemahaman bahasa alami kasus hukum
- Metadata Filtering: status keberlakuan peraturan & anotasi Putusan MK
"""
import re
import math
from typing import List, Tuple, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from engine.models import LegalArticle, RegulationStatus


def tokenize(text: str) -> List[str]:
    """Tokenize Indonesian legal text into normalized lowercase tokens."""
    clean_text = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [t for t in clean_text.split() if len(t) > 1]
    return tokens


class LegalRetriever:
    """Hybrid Retriever combining BM25 keyword matching, semantic vector scoring, and PostgreSQL FTS."""

    def __init__(self, articles: Optional[List[LegalArticle]] = None, db: Optional[Any] = None):
        self.db = db
        self.articles: List[LegalArticle] = articles or []
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_tokens: List[List[str]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

        if self.articles:
            self._index_articles()
        elif self.db:
            self.reload_from_db()

    def reload_from_db(self):
        """Loads all articles from PostgreSQL database and builds index."""
        if not self.db:
            return
        db_articles = self.db.get_all_articles_as_models()
        if db_articles:
            self.articles = db_articles
            self._index_articles()

    def add_articles(self, new_articles: List[LegalArticle]):
        self.articles.extend(new_articles)
        self._index_articles()

    def _index_articles(self):
        """Build BM25 index and TF-IDF semantic vector space."""
        self.corpus_tokens = []
        doc_freq: Dict[str, int] = {}

        for article in self.articles:
            doc_str = (
                f"{article.regulation_name} {article.regulation_number} "
                f"Pasal {article.article_number} {article.content} "
                f"{article.explanation or ''} {article.chapter or ''} {article.notes or ''}"
            )
            tokens = tokenize(doc_str)
            self.corpus_tokens.append(tokens)

            # Document frequency for TF-IDF
            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1

        self.bm25 = BM25Okapi(self.corpus_tokens)

        # Compute IDF
        n_docs = len(self.articles)
        self.vocabulary = {term: idx for idx, term in enumerate(doc_freq.keys())}
        self.idf = {
            term: math.log((n_docs + 1) / (df + 1)) + 1.0
            for term, df in doc_freq.items()
        }

    def _vectorize(self, tokens: List[str]) -> Dict[str, float]:
        """Generate normalized TF-IDF vector dict."""
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0

        vec: Dict[str, float] = {}
        sum_sq = 0.0
        for t, freq in tf.items():
            if t in self.idf:
                weight = (freq / len(tokens)) * self.idf[t]
                vec[t] = weight
                sum_sq += weight * weight

        magnitude = math.sqrt(sum_sq) or 1.0
        return {t: w / magnitude for t, w in vec.items()}

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse TF-IDF vectors."""
        score = 0.0
        for term, weight in vec_a.items():
            if term in vec_b:
                score += weight * vec_b[term]
        return score

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_status: Optional[RegulationStatus] = None,
        alpha_bm25: float = 0.5,
        alpha_semantic: float = 0.5
    ) -> List[Tuple[LegalArticle, float]]:
        """
        Hybrid search combining BM25 Okapi and Semantic Cosine similarity.
        
        Args:
            query: User's question or legal search query
            top_k: Number of relevant articles to retrieve
            filter_status: Optional filter by regulation status
            alpha_bm25: Weight for BM25 keyword score (0.0 to 1.0)
            alpha_semantic: Weight for semantic similarity score (0.0 to 1.0)
        """
        if not self.articles or not self.bm25:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 1. BM25 Scores
        bm25_raw_scores = self.bm25.get_scores(query_tokens)
        max_bm25 = max(bm25_raw_scores) if max(bm25_raw_scores) > 0 else 1.0
        normalized_bm25 = [score / max_bm25 for score in bm25_raw_scores]

        # 2. Semantic Vector Scores
        query_vec = self._vectorize(query_tokens)
        semantic_scores = []
        for doc_tokens in self.corpus_tokens:
            doc_vec = self._vectorize(doc_tokens)
            sim = self._cosine_similarity(query_vec, doc_vec)
            semantic_scores.append(sim)

        # 3. Combine scores & filter
        scored_articles: List[Tuple[LegalArticle, float]] = []
        for i, article in enumerate(self.articles):
            if filter_status and article.status != filter_status:
                continue

            hybrid_score = (alpha_bm25 * normalized_bm25[i]) + (alpha_semantic * semantic_scores[i])

            # Bonus for exact article number match (e.g., query mentions "340" and article is "340")
            if article.article_number in query:
                hybrid_score += 0.3

            # Special boost if the article is a relevant Constitutional Court (MK) ruling
            if "tersangka" in query_tokens and "21/puu-xii/2014" in article.regulation_number.lower():
                hybrid_score += 0.35

            scored_articles.append((article, hybrid_score))

        # 4. Dynamic PostgreSQL FTS Hybrid Boost (if database connection available)
        if self.db:
            try:
                db_matches = self.db.search_articles_as_models(query, limit=top_k * 2)
                existing_map = {f"{a.regulation_number}_{a.article_number}": idx for idx, (a, s) in enumerate(scored_articles)}
                for rank_idx, db_art in enumerate(db_matches):
                    fts_boost = max(0.15, 0.45 - (rank_idx * 0.05))
                    key = f"{db_art.regulation_number}_{db_art.article_number}"
                    if key in existing_map:
                        idx = existing_map[key]
                        art, old_score = scored_articles[idx]
                        scored_articles[idx] = (art, old_score + fts_boost)
                    else:
                        # Article in PostgreSQL but not in in-memory corpus
                        scored_articles.append((db_art, 0.6 + fts_boost))
            except Exception:
                pass

        # Sort descending by hybrid score
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return scored_articles[:top_k]
