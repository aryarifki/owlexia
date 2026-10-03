"""Legal AI Agent System Orchestrator.

Menggabungkan:
1. Proactive Fact Evaluator & Clarification Loop
2. Hybrid Legal Retriever (BM25 + Semantic Cosine)
3. IRAC Legal Reasoner
"""
from typing import Dict, Any, Optional, List
from engine.models import (
    FactCompleteness,
    ClarificationQuestion,
    LegalAssessment,
    LegalArticle,
    RegulationStatus
)
from engine.retriever import LegalRetriever
from engine.proactive_agent import ProactiveCaseAnalyzer
from engine.reasoner import LegalReasoner
from seed_regulations import get_all_articles


class LegalAgentResponse:
    def __init__(
        self,
        is_clarification_mode: bool,
        message: str,
        completeness: FactCompleteness,
        questions: Optional[List[ClarificationQuestion]] = None,
        assessment: Optional[LegalAssessment] = None,
        retrieved_articles: Optional[List[LegalArticle]] = None
    ):
        self.is_clarification_mode = is_clarification_mode
        self.message = message
        self.completeness = completeness
        self.questions = questions or []
        self.assessment = assessment
        self.retrieved_articles = retrieved_articles or []


class LegalAgentOrchestrator:
    """Master orchestrator for the Indonesian Legal AI Agent."""

    def __init__(self, custom_articles: Optional[List[LegalArticle]] = None):
        articles = list(custom_articles or get_all_articles())
        
        # Load any additional articles ingested via pipeline
        from pathlib import Path
        import json
        parsed_file = Path(__file__).resolve().parent.parent / "data" / "parsed_regulations.json"
        if parsed_file.exists():
            try:
                with open(parsed_file, "r", encoding="utf-8") as f:
                    stored_data = json.load(f)
                    for item in stored_data:
                        articles.append(LegalArticle(**item))
            except Exception:
                pass

        self.retriever = LegalRetriever(articles)
        self.case_analyzer = ProactiveCaseAnalyzer()
        self.reasoner = LegalReasoner()
        try:
            from engine.prompt_manager import PromptManager
            self.prompt_manager = PromptManager()
        except Exception:
            self.prompt_manager = None

        try:
            from engine.database import OwlexiaDatabase
            self.db = OwlexiaDatabase()
        except Exception:
            self.db = None

    def _classify_intent(self, query: str) -> str:
        q = query.lower().strip()

        # 1. Pertanyaan seputar isi basis data / koleksi regulasi
        meta_phrases = [
            "apa saja peraturan", "peraturan apa saja", "peraturan apa aja",
            "undang-undang apa saja", "undang undang apa saja", "uu apa saja", "uu apa aja",
            "apa yang ada di database", "isi database", "database kamu", "database anda",
            "basis data kamu", "basis data anda", "koleksi hukum", "koleksi peraturan",
            "daftar peraturan", "daftar undang-undang", "daftar uu", "ada data apa saja",
            "data hukum apa saja", "regulasi apa saja", "peraturan yang ada",
            "peraturan yang tersimpan", "kamu punya peraturan apa", "kamu punya uu apa",
            "tersimpan di database", "isi basis data", "list peraturan", "list uu"
        ]
        if any(p in q for p in meta_phrases):
            return "INTENT_DATABASE_METADATA"

        # 2. Greeting / Perkenalan diri
        greetings = [
            "halo", "hai", "hello", "hi", "selamat pagi", "selamat siang",
            "selamat sore", "selamat malam", "siapa kamu", "kamu siapa",
            "apa itu owlexia", "siapa owlexia", "bisa bantu apa", "apa fungsi kamu",
            "kamu bisa apa", "bisa apa saja"
        ]
        words = q.split()
        if len(words) <= 6 and any(g in q for g in greetings):
            return "INTENT_GREETING"

        return "INTENT_LEGAL_ANALYSIS"

    def _format_database_metadata_response(self) -> LegalAgentResponse:
        total_articles = 0
        db_regulations = []
        if self.db and self.db.test_connection():
            total_articles = self.db.get_total_articles_count()
            db_regulations = self.db.get_regulations_list()
        else:
            total_articles = len(self.retriever.articles)

        # Kelompokkan regulasi berdasarkan kategori
        crawled_list = []
        for r in db_regulations:
            slug = r.get("peraturan_id_slug", "")
            if slug not in ["kuhp-wvs-1946", "uu-1-2023", "uu-8-1981", "putusan-mk-21-2014"]:
                crawled_list.append(f"• **{r.get('judul')}** ({r.get('total_pasal', 0)} pasal terindeks)")

        crawled_section = ""
        if crawled_list:
            crawled_bullets = "\n".join(crawled_list[:5])
            crawled_section = f"\n\n**5. Regulasi Terkini Hasil Crawling (Peraturan.go.id):**\n{crawled_bullets}"

        msg = (
            f"Halo! Di dalam basis data **OWLEXIA** (`owlexia_db`), saat ini telah terindeks "
            f"sebanyak **{total_articles} norma pasal** dari berbagai undang-undang resmi Republik Indonesia "
            "dan yurisprudensi penting, yang siap dianalisis secara akurat:\n\n"
            "**1. Kitab Undang-Undang Hukum Pidana (KUHP Lama - WvS 1946)**\n"
            "• Mengatur delik-delik konvensional seperti pembunuhan biasa (Pasal 338), pembunuhan berencana (Pasal 340), "
            "penganiayaan orang tua (Pasal 356 ke-1), perbarengan tindak pidana (Pasal 65), dan alasan pemaaf kejiwaan (Pasal 44).\n\n"
            "**2. KUHP Nasional Baru (UU No. 1 Tahun 2023)**\n"
            "• Kodifikasi pembaharuan hukum pidana Indonesia, mencakup Pasal 458 & 459, klausul pemberatan 1/3 keluarga (Pasal 58 huruf c), "
            "dan pedoman pidana transisi.\n\n"
            "**3. Hukum Acara Pidana (KUHAP - UU No. 8 Tahun 1981)**\n"
            "• Mengatur hukum formil penegakan hukum: definisi tersangka (Pasal 1 angka 14), praperadilan (Pasal 77), dan alat bukti sah (Pasal 184).\n\n"
            "**4. Yurisprudensi Mahkamah Konstitusi (MK)**\n"
            "• **Putusan MK No. 21/PUU-XII/2014**: Menetapkan bahwa penetapan tersangka sah hanya jika didasarkan minimal 2 alat bukti sah "
            "dan telah memeriksa calon tersangka terlebih dahulu."
            f"{crawled_section}\n\n"
            "---\n"
            "💡 **Apa yang dapat Anda tanyakan?**\n"
            "• Anda dapat menanyakan analisis kasus konkret secara bebas (misal: konsekuensi pidana, hak tersangka, unsur delik).\n"
            "• Anda juga dapat menambahkan undang-undang atau peraturan baru kapan saja dengan mengklik tombol **'+ Ingest Regulasi'** di menu atas."
        )

        return LegalAgentResponse(
            is_clarification_mode=False,
            message=msg,
            completeness=FactCompleteness(score=1.0),
            assessment=None,
            retrieved_articles=[]
        )

    def _format_greeting_response(self) -> LegalAgentResponse:
        msg = (
            "Halo! Saya **OWLEXIA**, asisten intelijen dan penalaran hukum berbasis regulasi resmi Republik Indonesia.\n\n"
            "Saya dirancang untuk membantu Anda memahami persoalan hukum yang rumit dengan prinsip **kehati-hatian yuridis**:\n"
            "• **Analisis Proaktif**: Bila Anda menguraikan kasus peristiwa pidana, saya akan mendalami fakta terlebih dahulu sebelum mengambil kesimpulan definitif.\n"
            "• **Dualisme Regulasi**: Mampu membandingkan KUHP WvS (lama) dan KUHP Baru (UU No. 1 Tahun 2023) beserta putusan Mahkamah Konstitusi.\n"
            "• **Koneksi Resmi Peraturan.go.id**: Memiliki basis data PostgreSQL yang dapat di-ingest dengan undang-undang baru kapan saja.\n\n"
            "Silakan ceritakan permasalahan hukum Anda atau tanyakan pasal perundang-undangan tertentu!"
        )
        return LegalAgentResponse(
            is_clarification_mode=False,
            message=msg,
            completeness=FactCompleteness(score=1.0),
            assessment=None,
            retrieved_articles=[]
        )

    def process_query(
        self,
        user_query: str,
        case_context: Optional[Dict[str, Any]] = None,
        force_assessment: bool = False
    ) -> LegalAgentResponse:
        """
        Processes user query with proactive confidence thresholding.
        
        Args:
            user_query: The question from the user.
            case_context: Answers from prior clarification rounds.
            force_assessment: If True, skips clarification and generates assessment directly.
        """
        case_context = case_context or {}

        # 0. Intent Classification: Cek apakah user menanyakan database atau sekadar sapaan
        intent = self._classify_intent(user_query)
        if intent == "INTENT_DATABASE_METADATA":
            return self._format_database_metadata_response()
        elif intent == "INTENT_GREETING" and not force_assessment and not case_context:
            return self._format_greeting_response()

        # 1. Evaluasi Kelengkapan Fakta & Proaktivitas Agen
        completeness = self.case_analyzer.evaluate_facts(user_query, case_context)

        # 2. Jika fakta belum lengkap dan belum ada paksaan jawaban -> Masuk Clarification Loop
        if completeness.needs_clarification and not force_assessment and not case_context:
            questions = self.case_analyzer.generate_clarification_questions(user_query, completeness)
            
            # Buat pesan pengantar proaktif
            reasons_bullets = "\n".join([f"- {r}" for r in completeness.clarification_reasons])
            intro_msg = (
                "⚖️ **Analisis Pendahuluan & Sikap Kehati-hatian Hukum**\n\n"
                "Pertanyaan Anda menyangkut persoalan hukum pidana yang memiliki konsekuensi sanksi sangat berat atau implikasi hak asasi yang mendasar. "
                "Sebagai asisten hukum yang teliti, saya tidak serta merta mengambil kesimpulan definitif karena rumusan pasal dan beratnya hukuman "
                "sangat bergantung pada variabel fakta peristiwa yang spesifik:\n\n"
                f"{reasons_bullets}\n\n"
                "Mohon klarifikasi beberapa rincian berikut agar analisis hukum yang saya berikan sepenuhnya akurat dan relevan dengan situasi Anda:"
            )

            return LegalAgentResponse(
                is_clarification_mode=True,
                message=intro_msg,
                completeness=completeness,
                questions=questions
            )

        # 3. Jika fakta sudah memadai atau user sudah menjawab klarifikasi -> Lakukan Hybrid Retrieval
        retrieved_with_scores = self.retriever.search(user_query, top_k=5)
        retrieved_articles = [art for art, score in retrieved_with_scores]

        # 4. IRAC Legal Reasoning
        assessment = self.reasoner.analyze(
            query=user_query,
            retrieved_articles=retrieved_articles,
            completeness=completeness,
            context=case_context
        )

        return LegalAgentResponse(
            is_clarification_mode=False,
            message="Analisis hukum komprehensif berhasil disusun berdasarkan regulasi positif Republik Indonesia.",
            completeness=completeness,
            assessment=assessment,
            retrieved_articles=retrieved_articles
        )
