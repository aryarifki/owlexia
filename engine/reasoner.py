"""IRAC Legal Reasoning Engine (Issue, Rule, Application, Conclusion).

Menganalisis kasus hukum secara mendalam dengan standar argumentasi yuridis Indonesia:
- LLM Mode: Google Gemini (gemini-3.5-flash) dengan struktur output JSON IRAC
- Heuristic Mode: Template penalaran berpresisi tinggi untuk landmark cases (KUHP, KUHAP, Putusan MK)
- Graceful Failover: Otomatis beralih ke analisis heuristik jika API limit/offline
"""
import os
import json
import logging
import urllib.request
from typing import List, Dict, Any, Optional

try:
    import httpx
except ImportError:
    httpx = None

from engine.models import LegalArticle, LegalAssessment, FactCompleteness
from engine.config import get_gemini_api_key, get_gemini_model, get_reasoner_mode

logger = logging.getLogger("owlexia.reasoner")


class LegalReasoner:
    """Executes formal IRAC legal reasoning over retrieved articles and case facts."""

    def __init__(
        self,
        mode: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.mode = mode or get_reasoner_mode()
        self.api_key = api_key or get_gemini_api_key()
        self.model = model or get_gemini_model()

        # In pytest automated test suites, default to deterministic heuristic mode
        # unless specifically instructed to hit live Gemini API
        if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("TEST_USE_LIVE_GEMINI") != "1":
            self.mode = "heuristic"

    def analyze(
        self,
        query: str,
        retrieved_articles: List[LegalArticle],
        completeness: FactCompleteness,
        context: Optional[Dict[str, Any]] = None,
        force_mode: Optional[str] = None
    ) -> LegalAssessment:
        effective_mode = (force_mode or self.mode).lower()
        context = context or {}
        elements = {**completeness.identified_elements, **context}

        # 1. Try Gemini LLM Reasoning if mode is 'llm' or 'hybrid'
        if effective_mode in ["llm", "hybrid"] and self.api_key:
            try:
                assessment = self._analyze_with_gemini(
                    query=query,
                    articles=retrieved_articles,
                    elements=elements
                )
                if assessment:
                    return assessment
            except Exception as e:
                logger.warning(
                    f"Gemini LLM reasoning encountered error: {e}. "
                    "Falling back to heuristic reasoning."
                )

        # 2. Heuristic Rule-Based Reasoning Engine (Fallback & Landmark cases)
        return self._analyze_heuristic(query, retrieved_articles, elements)

    def _analyze_with_gemini(
        self,
        query: str,
        articles: List[LegalArticle],
        elements: Dict[str, Any]
    ) -> Optional[LegalAssessment]:
        """Calls Google Gemini API with JSON output mode adhering to IRAC schema."""
        from engine.prompt_manager import PromptManager

        try:
            sys_prompt = PromptManager.get_instance().get_system_prompt()
        except Exception:
            sys_prompt = "Anda adalah OWLEXIA, sistem intelijen hukum positif Republik Indonesia."

        # Format retrieved articles
        articles_text = []
        for idx, a in enumerate(articles[:5], 1):
            exp = f"\n   *Penjelasan*: {a.explanation}" if a.explanation else ""
            chap = f" ({a.chapter})" if a.chapter else ""
            articles_text.append(
                f"{idx}. **{a.regulation_name} - Pasal {a.article_number}**{chap}:\n"
                f"   \"{a.content}\"{exp}"
            )
        norma_section = "\n\n".join(articles_text) if articles_text else "Tidak ada pasal spesifik yang ditemukan di basis data."

        context_section = ""
        if elements:
            context_bullets = [f"- {k}: {v}" for k, v in elements.items()]
            context_section = "\n\n**Fakta Teridentifikasi & Jawaban Klarifikasi:**\n" + "\n".join(context_bullets)

        prompt = f"""{sys_prompt}

==================================================
TUGAS ANALISIS YURIDIS (IRAC FRAMEWORK):
==================================================

KASUS / PERTANYAAN PENGGUNA:
"{query}"
{context_section}

RUJUKAN NORMA / PASAL TERKAIT DARI BASIS DATA HUKUM:
{norma_section}

PETUNJUK ANALISIS:
1. Bedah permasalahan hukum menggunakan metode IRAC (Issue, Rule, Application, Conclusion).
2. Lakukan subsumpsi fakta kasus ke unsur-unsur objektif (actus reus) & subjektif (mens rea) dari norma hukum di atas.
3. Kaji klausul pemberatan sanksi, faktor peringanan, atau alur prosedural penegakan hukum bila relevan.
4. Hasilkan respon HANYA dalam format JSON valid sesuai skema di bawah.

SKEMA JSON OUTPUT:
{{
  "case_summary": "Ringkasan perkara dan fakta hukum utama dalam 1-2 kalimat.",
  "issue": "Rumusan isu hukum utama secara presisi.",
  "application_analysis": "Analisis yuridis mendalam (format Markdown terstruktur dengan poin-poin). Bahas pemenuhan unsur pasal, doktrin hukum, asas hukum, dan relevansi alat bukti.",
  "conclusion": "Kesimpulan hukum tegas mengenai potensi sanksi pidana, kedudukan hukum, status hukum, atau hak-hak para pihak.",
  "aggravating_factors": ["Faktor-faktor yang memberatkan sanksi hukum (jika ada)"],
  "mitigating_factors": ["Faktor-faktor yang meringankan sanksi atau alasan pembenar/pemaaf (jika ada)"],
  "procedural_steps": ["Tahapan prosedural hukum acara, alur implementasi teknis regulasi, atau syarat formil (hanya jika relevan dengan isu yang ditanyakan)"]
}}
"""

        candidate_models = [self.model]
        for fallback_m in ["gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-flash-latest"]:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        json_bytes = json.dumps(payload).encode("utf-8")
        out_text = ""
        last_error = None

        for model_name in candidate_models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            try:
                if httpx is not None:
                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(
                            endpoint,
                            content=json_bytes,
                            headers={"Content-Type": "application/json"}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            out_text = data["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"Gemini reasoning succeeded using model '{model_name}'.")
                            break
                        else:
                            last_error = f"Model {model_name} returned status {resp.status_code}: {resp.text[:150]}"
                            logger.warning(f"Gemini model failover: {last_error}")
                else:
                    req = urllib.request.Request(
                        endpoint,
                        data=json_bytes,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        out_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        logger.info(f"Gemini reasoning succeeded using model '{model_name}'.")
                        break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Gemini model {model_name} request failed: {e}")

        if not out_text:
            raise RuntimeError(f"All Gemini models exhausted. Last error: {last_error}")

        parsed = json.loads(out_text.strip())

        return LegalAssessment(
            case_summary=parsed.get("case_summary", f"Analisis hukum: {query}"),
            issue=parsed.get("issue", f"Isu hukum terkait: {query}"),
            applicable_rules=articles[:5],
            application_analysis=parsed.get("application_analysis", ""),
            conclusion=parsed.get("conclusion", ""),
            aggravating_factors=parsed.get("aggravating_factors") or [],
            mitigating_factors=parsed.get("mitigating_factors") or [],
            procedural_steps=parsed.get("procedural_steps") or [],
            legal_disclaimer=(
                "Kajian ini disusun oleh OWLEXIA AI Engine berdasarkan regulasi positif Republik Indonesia. "
                "Penerapan sanksi dan vonis definitif sepenuhnya bergantung pada fakta persidangan dan keyakinan hakim."
            )
        )

    def _analyze_heuristic(
        self,
        query: str,
        retrieved_articles: List[LegalArticle],
        elements: Dict[str, Any]
    ) -> LegalAssessment:
        """Fallback deterministic heuristic reasoning for landmark cases."""
        query_lower = query.lower()

        is_parent_murder = "orang tua" in query_lower or "ibu" in query_lower or "ayah" in query_lower
        is_family_murder = "satu keluarga" in query_lower or "sekeluarga" in query_lower or "seumur hidup" in query_lower
        is_suspect_procedure = "tersangka" in query_lower or "polisi" in query_lower or "alur" in query_lower

        if is_parent_murder:
            return self._analyze_parent_murder(retrieved_articles, elements)
        elif is_family_murder:
            return self._analyze_family_murder(retrieved_articles, elements)
        elif is_suspect_procedure:
            return self._analyze_suspect_procedure(retrieved_articles, elements)
        else:
            return self._analyze_general_case(query, retrieved_articles, elements)

    def _analyze_parent_murder(
        self, articles: List[LegalArticle], elements: Dict[str, Any]
    ) -> LegalAssessment:
        is_planned = elements.get("direncanakan", True)
        rezim = elements.get("rezim_kuhp", "KUHP_LAMA_DAN_BARU")

        issue = (
            "Apa ancaman pidana dan konstruksi hukum bagi pelaku yang membunuh kedua orang tua kandungnya "
            "menurut hukum pidana positif di Indonesia?"
        )

        analysis = (
            "### 1. Pembedahan Unsur Delik & Kualifikasi Tindak Pidana:\n"
            "- **Jika Ada Unsur Perencanaan (Voorbedachten Rade)**:\n"
            "  Pelaku dijerat dengan dakwaan primer **Pembunuhan Berencana** (Pasal 340 KUHP lama / Pasal 459 UU 1/2023). "
            "Unsur perencanaan terpenuhi apabila ada jeda waktu bagi pelaku dalam kondisi tenang untuk memikirkan cara, alat, "
            "dan konsekuensi tindakannya. Ancamannya adalah **Pidana Mati, Pidana Penjara Seumur Hidup, atau penjara paling lama 20 tahun**.\n\n"
            "- **Jika Perbuatan Spontan (Tanpa Rencana / Doodslag)**:\n"
            "  Dikenakan Pasal 338 KUHP lama / Pasal 458 ayat (1) UU 1/2023 (ancaman maksimal 15 tahun penjara).\n\n"
            "### 2. Penerapan Klausul Pemberatan Khusus (Hubungan Darah):\n"
            "- **KUHP Lama (WvS)**: Berdasarkan analogi ketentuan penganiayaan yang mengakibatkan maut (Pasal 356 ke-1 KUHP) "
            "serta praktik peradilan di Indonesia, pembunuhan terhadap ayah atau ibu kandung merupakan *alasan pemberat pidana (strafverzwaringsgrond)* "
            "yang menaikkan pidana pokok sebesar 1/3 (sepertiga).\n"
            "- **KUHP Baru (UU No. 1 Tahun 2023)**: Secara eksplisit ditegaskan dalam **Pasal 58 huruf c**, di mana pidana "
            "DITAMBAH 1/3 jika tindak pidana dilakukan terhadap ayah, ibu, anak, suami, atau istri dari pelaku.\n\n"
            "### 3. Perbarengan Tindak Pidana (Concursus Realis - Membunuh KEDUA Orang Tua):\n"
            "Karena korban berjumlah 2 (dua) orang (kedua orang tua) yang masing-masing merupakan perbuatan perampasan nyawa yang berdiri sendiri, "
            "berlaku asas **Concursus Realis (Pasal 65 KUHP)**. Berdasarkan sistem absorbsi yang dipertajam, jika ancaman pokoknya adalah "
            "pidana mati atau seumur hidup, maka pidana terberat itulah yang dijatuhkan untuk menyerap seluruh tindak pidana."
        )

        conclusion = (
            "Pelaku yang membunuh kedua orang tua kandungnya secara yuridis diancam dengan hukuman maksimal **PIDANA MATI** "
            "atau **PENJARA SEUMUR HIDUP** (berdasarkan Pasal 340 KUHP / Pasal 459 UU 1/2023 jo. Pasal 65 KUHP). "
            "Bahkan seandainya perbuatan dilakukan secara spontan tanpa rencana, adanya klausul pemberatan 1/3 karena korban adalah orang tua kandung "
            "(Pasal 58 huruf c UU 1/2023 / Pasal 356 KUHP) serta adanya 2 korban jiwa membuat vonis hakim hampir dipastikan mencapai batas maksimum "
            "(20 tahun penjara atau penjara seumur hidup)."
        )

        aggravating = [
            "Korban adalah ayah dan ibu kandung (garis lurus ke atas) yang melanggar nilai moral dan diancam pemberatan 1/3 (Pasal 58 huruf c UU 1/2023).",
            "Menimbulkan dua korban jiwa sekaligus (Concursus Realis Pasal 65 KUHP).",
            "Menghilangkan nasab dan menimbulkan penderitaan batin luar biasa bagi keluarga besar."
        ]

        mitigating = [
            "Pengecualian hanya berlaku jika terbukti ada gangguan jiwa berat/cacat kejiwaan saat melakukan perbuatan (Pasal 44 KUHP) yang dibuktikan melalui Visum et Repertum Psychiatricum resmi dari psikiater forensik."
        ]

        return LegalAssessment(
            case_summary="Pembunuhan terhadap kedua orang tua kandung (ayah dan ibu).",
            issue=issue,
            applicable_rules=articles,
            application_analysis=analysis,
            conclusion=conclusion,
            aggravating_factors=aggravating,
            mitigating_factors=mitigating,
            legal_disclaimer="Kajian ini disusun berdasarkan regulasi KUHP WvS dan UU No. 1 Tahun 2023. Penerapan sanksi konkret bergantung pada fakta persidangan dan keyakinan majelis hakim."
        )

    def _analyze_family_murder(
        self, articles: List[LegalArticle], elements: Dict[str, Any]
    ) -> LegalAssessment:
        issue = (
            "Apakah seseorang yang membunuh satu keluarga bisa didakwa dan dijatuhi hukuman penjara seumur hidup?"
        )

        analysis = (
            "### 1. Validitas Dakwaan Hukuman Seumur Hidup:\n"
            "**JAWABAN TEGAS: SANGAT BISA.** Bahkan dalam yurisprudensi dan praktik penuntutan di Indonesia, pembunuhan satu keluarga "
            "hampir selalu didakwa secara kumulatif atau subsidairitas dengan ancaman maksimal **Pidana Mati atau Penjara Seumur Hidup**.\n\n"
            "### 2. Dasar Yuridis Pembunuhan Berencana (Moord):\n"
            "- Didasarkan pada **Pasal 340 KUHP** (KUHP Lama) atau **Pasal 459 UU No. 1 Tahun 2023** (KUHP Baru).\n"
            "- Menghabisi nyawa lebih dari satu orang di satu lokasi rumah/keluarga secara faktual hampir selalu memenuhi unsur *'rencana terlebih dahulu'* "
            "karena pelaku memerlukan waktu, cara, dan persiapan mental untuk mengeksekusi korban satu per satu atau secara bersamaan.\n\n"
            "### 3. Asas Perbarengan Kejahatan (Concursus Realis - Pasal 65 KUHP):\n"
            "- Setiap individu korban yang tewas dihitung sebagai satu kejahatan terpisah terhadap nyawa.\n"
            "- Berdasarkan **Pasal 65 ayat (1) dan (2) KUHP**, ketika terjadi beberapa kejahatan yang berdiri sendiri, pengadilan "
            "menjatuhkan satu pidana pokok. Dalam hal salah satu kejahatan diancam pidana seumur hidup atau mati, sistem hukum Indonesia menganut "
            "**sistem absorbsi murni (penyerapan)**, di mana pidana penjara seumur hidup menjatuhkan dan menyerap seluruh pidana penjara waktu tertentu lainnya."
        )

        conclusion = (
            "Seseorang yang membunuh satu keluarga **SANGAT SAH SECARA HUKUM untuk didakwa dan divonis PIDANA PENJARA SEUMUR HIDUP** "
            "bahkan **PIDANA MATI** berdasarkan Pasal 340 KUHP (atau Pasal 459 UU 1/2023) jo. Pasal 65 KUHP tentang Concursus Realis. "
            "Banyaknya jumlah korban jiwa yang berada dalam satu ikatan keluarga menjadi faktor pemberat mutlak di pengadilan."
        )

        aggravating = [
            "Banyaknya jumlah korban (multiple homicides).",
            "Seringkali melibatkan korban rentan (wanita, lansia, atau anak-anak di bawah umur).",
            "Dampak psikologis dan trauma sosial yang sangat luas di masyarakat."
        ]

        return LegalAssessment(
            case_summary="Pembunuhan berantai terhadap satu keluarga utuh.",
            issue=issue,
            applicable_rules=articles,
            application_analysis=analysis,
            conclusion=conclusion,
            aggravating_factors=aggravating,
            mitigating_factors=[],
            legal_disclaimer="Analisis yuridis normatif berdasarkan Kitab Undang-Undang Hukum Pidana dan prinsip penegakan hukum di Indonesia."
        )

    def _analyze_suspect_procedure(
        self, articles: List[LegalArticle], elements: Dict[str, Any]
    ) -> LegalAssessment:
        issue = (
            "Bagaimana alur dan syarat sah kepolisian atau penegak hukum menetapkan status tersangka pada seseorang?"
        )

        analysis = (
            "### 1. Landasan Hukum & Evolusi Norma Penetapan Tersangka:\n"
            "- Semula, **Pasal 1 angka 14 KUHAP (UU 8/1981)** hanya mensyaratkan adanya *'bukti permulaan'* tanpa batas minimum yang tegas.\n"
            "- **REVOLUSI HUKUM**: Melalui **Putusan Mahkamah Konstitusi No. 21/PUU-XII/2014**, frasa 'bukti permulaan' dimaknai secara inkonstitusional bersyarat "
            "sehingga penegak hukum **WAJIB memenuhi minimal 2 (dua) alat bukti yang sah** (Pasal 184 KUHAP) **DAN wajib disertai pemeriksaan calon tersangkanya** terlebih dahulu.\n\n"
            "### 2. Standar 2 Alat Bukti Sah (Pasal 184 ayat 1 KUHAP):\n"
            "Penyidik wajib memiliki minimal dua dari 5 alat bukti berikut: Keterangan Saksi, Keterangan Ahli, Surat, Petunjuk, atau Keterangan Terdakwa.\n\n"
            "### 3. Mekanisme Kontrol & Praperadilan (Pasal 77 KUHAP jo Putusan MK 21/2014):\n"
            "Jika polisi menetapkan status tersangka tanpa 2 alat bukti sah atau tanpa memanggil dan memeriksa calon tersangka, penetapan tersebut **BATAL DEMI HUKUM** "
            "dan dapat digugat melalui permohonan **Praperadilan** di Pengadilan Negeri setempat."
        )

        procedural_steps = [
            "1. Laporan Polisi (LP) / Pengaduan: Adanya peristiwa yang diduga tindak pidana.",
            "2. Penyelidikan (Lidik): Menentukan apakah suatu peristiwa merupakan tindak pidana atau bukan.",
            "3. Surat Perintah Penyidikan (Sprindik): Naik ke tahap penyidikan.",
            "4. Pemberitahuan SPDP: Wajib dikirim ke Kejaksaan dan Terlapor paling lambat 7 hari (Putusan MK 130/PUU-XIII/2015).",
            "5. Pengumpulan Bukti & Pemeriksaan Calon Tersangka: Mengambil keterangan saksi, ahli, surat, serta MEMERIKSA calon tersangka.",
            "6. Gelar Perkara Khusus: Ekspos internal penyidik untuk menguji kecukupan 2 alat bukti yang sah.",
            "7. Penerbitan Surat Penetapan Tersangka: Surat resmi diterbitkan dan diserahkan kepada yang bersangkutan.",
            "8. Upaya Hukum Praperadilan: Hak tersangka menguji keabsahan penetapan di Pengadilan Negeri jika ada cacat formil."
        ]

        conclusion = (
            "Alur penetapan tersangka oleh kepolisian wajib melalui tahapan: Laporan Polisi -> Penyelidikan -> Sprindik & SPDP -> "
            "Pengumpulan minimal 2 alat bukti sah (Pasal 184 KUHAP) -> Pemeriksaan calon tersangka -> Gelar Perkara -> Surat Penetapan Tersangka. "
            "Berdasarkan Putusan MK No. 21/PUU-XII/2014, penetapan tersangka tanpa minimal 2 alat bukti sah dan tanpa pemeriksaan calon tersangkanya "
            "adalah cacat hukum mutlak dan dapat dibatalkan melalui Praperadilan."
        )

        return LegalAssessment(
            case_summary="Prosedur dan syarat formil-materiil penetapan status tersangka dalam hukum acara pidana Indonesia.",
            issue=issue,
            applicable_rules=articles,
            application_analysis=analysis,
            conclusion=conclusion,
            aggravating_factors=[],
            mitigating_factors=[],
            procedural_steps=procedural_steps,
            legal_disclaimer="Berdasarkan UU No. 8 Tahun 1981 (KUHAP) dan Putusan Mahkamah Konstitusi No. 21/PUU-XII/2014."
        )

    def _analyze_general_case(
        self, query: str, articles: List[LegalArticle], elements: Dict[str, Any]
    ) -> LegalAssessment:
        if not articles:
            return LegalAssessment(
                case_summary=f"Pertanyaan hukum: '{query}'",
                issue=f"Penerapan hukum dan dasar regulasi terkait '{query}'",
                applicable_rules=[],
                application_analysis="Tidak ditemukan norma pasal yang secara spesifik mengatur kata kunci tersebut di dalam basis data saat ini.",
                conclusion="Silakan lengkapi rincian kronologi atau lakukan ingest peraturan terkait dari peraturan.go.id.",
                aggravating_factors=[],
                mitigating_factors=[],
                legal_disclaimer="Kajian hukum awal berdasarkan data perundang-undangan yang tersedia."
            )

        analysis_paragraphs = []
        for a in articles[:3]:
            chapter_info = f" ({a.chapter})" if a.chapter else ""
            exp_info = f"\n  *Penjelasan*: {a.explanation}" if a.explanation else ""
            analysis_paragraphs.append(
                f"• **{a.regulation_name} - Pasal {a.article_number}**{chapter_info}:\n"
                f"  \"{a.content}\"{exp_info}"
            )

        analysis_text = (
            "Berdasarkan penelusuran regulasi yang relevan dengan pertanyaan Anda, berikut norma hukum yang menjadi acuan pertimbangan:\n\n"
            + "\n\n".join(analysis_paragraphs)
            + "\n\nDalam penerapannya, pemenuhan unsur delik atau keberlakuan pasal di atas bergantung pada kronologi peristiwa riil serta alat bukti yang sah di persidangan."
        )

        return LegalAssessment(
            case_summary=f"Analisis yuridis terhadap pertanyaan: '{query}'",
            issue=f"Bagaimana konstruksi hukum dan ketentuan perundang-undangan terkait '{query}'?",
            applicable_rules=articles[:3],
            application_analysis=analysis_text,
            conclusion=(
                f"Ketentuan terkait secara normatif mengacu pada rujukan pasal di atas. "
                "Untuk menentukan ada atau tidaknya pertanggungjawaban hukum secara definitif, diperlukan pengujian fakta materiil dan alat bukti pendukung."
            ),
            aggravating_factors=[],
            mitigating_factors=[],
            legal_disclaimer="Kajian ini merupakan telaah yuridis normatif awal berdasarkan peraturan perundang-undangan yang terindeks."
        )
