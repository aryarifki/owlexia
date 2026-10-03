"""Proactive Legal Case Analyzer & Clarification Agent.

Bertugas mengevaluasi kelengkapan fakta hukum pengguna:
- Tidak serta merta mengambil keputusan jika fakta hukum belum lengkap / ambigu.
- Mendalami rincian kasus secara proaktif dengan menghasilkan pertanyaan klarifikasi berbobot.
- Menjelaskan konsekuensi yuridis mengapa pertanyaan tersebut krusial ditanyakan.
"""
from typing import List, Dict, Any, Optional
from engine.models import FactCompleteness, ClarificationQuestion, ClarificationOption


class ProactiveCaseAnalyzer:
    """Evaluates case facts and generates proactive clarification questions."""

    def evaluate_facts(self, query: str, context: Optional[Dict[str, Any]] = None) -> FactCompleteness:
        """
        Analyzes the query and extracts identified vs missing legal elements.
        Computes completeness score.
        """
        query_lower = query.lower()
        context = context or {}

        # Deteksi Topik Kasus
        is_homicide = any(w in query_lower for w in ["bunuh", "membunuh", "pembunuhan", "nyawa", "mati"])
        is_suspect_procedure = any(w in query_lower for w in ["tersangka", "status tersangka", "polisi", "pengadilan menetapkan", "sprindik", "spdp", "alat bukti"])

        identified = {}
        missing = []
        reasons = []

        if is_homicide:
            # 1. Elemen Korban Orang Tua
            if any(w in query_lower for w in ["orang tua", "ibu", "ayah", "bapak", "kedua orang tuanya", "mama", "papa"]):
                identified["korban_orang_tua"] = True
            elif "korban_orang_tua" in context:
                identified["korban_orang_tua"] = context["korban_orang_tua"]
            else:
                missing.append("hubungan_korban")
                reasons.append("Hubungan kekeluargaan sedarah menentukan adanya pasal pemberat sanksi pidana sepertiga (1/3).")

            # 2. Elemen Perencanaan (Voorbedachten Rade)
            if any(w in query_lower for w in ["berencana", "rencana", "merencanakan", "disengaja dan disiapkan"]):
                identified["direncanakan"] = True
            elif any(w in query_lower for w in ["spontan", "tiba-tiba", "pertengkaran mendadak", "emosi sesaat", "tidak berencana"]):
                identified["direncanakan"] = False
            elif "direncanakan" in context:
                identified["direncanakan"] = context["direncanakan"]
            else:
                missing.append("unsur_perencanaan")
                reasons.append(
                    "Unsur perencanaan membedakan pembunuhan biasa (Pasal 338 KUHP, maks 15 tahun) dengan pembunuhan berencana "
                    "(Pasal 340 KUHP / Pasal 459 UU 1/2023, ancaman pidana mati atau seumur hidup)."
                )

            # 3. Elemen Jumlah Korban / Satu Keluarga (Concursus)
            if any(w in query_lower for w in ["satu keluarga", "sekeluarga", "banyak orang", "kedua orang tua", "beberapa korban"]):
                identified["multiple_victims"] = True
            elif "multiple_victims" in context:
                identified["multiple_victims"] = context["multiple_victims"]

            # 4. Elemen Alasan Pemaaf / Kejiwaan (Pasal 44)
            if any(w in query_lower for w in ["gila", "gangguan jiwa", "skizofrenia", "depresi berat"]):
                identified["gangguan_kejiwaan"] = True
            elif "gangguan_kejiwaan" in context:
                identified["gangguan_kejiwaan"] = context["gangguan_kejiwaan"]
            else:
                missing.append("kondisi_kejiwaan_atau_daya_paksa")
                reasons.append("Kondisi kejiwaan pelaku menentukan apakah berlaku alasan pemaaf (Pasal 44 KUHP) yang menghapuskan penjatuhan pidana.")

            # 5. Elemen Tempus Delicti (Waktu Kejadian - KUHP Lama vs Baru)
            if any(w in query_lower for w in ["tahun 2026", "kuhp baru", "setelah 2026"]):
                identified["rezim_kuhp"] = "KUHP_BARU_UU_1_2023"
            elif any(w in query_lower for w in ["sebelum 2026", "sekarang", "kuhp lama"]):
                identified["rezim_kuhp"] = "KUHP_LAMA_WVS"
            elif "rezim_kuhp" in context:
                identified["rezim_kuhp"] = context["rezim_kuhp"]
            else:
                missing.append("waktu_peristiwa_tempus")
                reasons.append("Masa transisi hukum: Peristiwa sebelum 2 Jan 2026 tunduk pada WvS, setelahnya tunduk pada UU 1/2023 dengan ases lex favor reo.")

            total_factors = 5
            known_factors = len(identified)
            score = round(known_factors / total_factors, 2)
            needs_clarification = score < 0.85

            return FactCompleteness(
                score=score,
                identified_elements=identified,
                missing_critical_elements=missing,
                needs_clarification=needs_clarification,
                clarification_reasons=reasons
            )

        elif is_suspect_procedure:
            # 1. Elemen Minimal 2 Alat Bukti Sah
            if any(w in query_lower for w in ["2 alat bukti", "dua alat bukti", "alat bukti sah", "bukti permulaan"]):
                identified["alat_bukti_cukup"] = True
            elif "alat_bukti_cukup" in context:
                identified["alat_bukti_cukup"] = context["alat_bukti_cukup"]
            else:
                missing.append("kecukupan_alat_bukti")
                reasons.append("Putusan MK No. 21/PUU-XII/2014 mewajibkan minimal 2 alat bukti yang sah sesuai Pasal 184 KUHAP sebelum menetapkan tersangka.")

            # 2. Elemen Pemeriksaan Calon Tersangka
            if any(w in query_lower for w in ["sudah diperiksa", "pernah diperiksa sebagai saksi", "berita acara pemeriksaan"]):
                identified["sudah_diperiksa_calon"] = True
            elif "sudah_diperiksa_calon" in context:
                identified["sudah_diperiksa_calon"] = context["sudah_diperiksa_calon"]
            else:
                missing.append("pemeriksaan_calon_tersangka")
                reasons.append("Sesuai Putusan MK 21/PUU-XII/2014, seseorang wajib terlebih dahulu diperiksa sebagai calon tersangka/saksi sebelum ditetapkan statusnya.")

            # 3. Elemen Gelar Perkara & SPDP
            if any(w in query_lower for w in ["spdp", "gelar perkara", "sprindik"]):
                identified["tahap_administrasi"] = True
            elif "tahap_administrasi" in context:
                identified["tahap_administrasi"] = context["tahap_administrasi"]
            else:
                missing.append("administrasi_penyidikan_spdp")
                reasons.append("SPDP wajib dikirimkan penyidik kepada terlapor dan penuntut umum maksimal 7 hari (Putusan MK 130/PUU-XIII/2015).")

            # 4. Keperluan Praperadilan
            if any(w in query_lower for w in ["praperadilan", "gugat penetapan", "membatalkan status"]):
                identified["fokus_praperadilan"] = True
            elif "fokus_praperadilan" in context:
                identified["fokus_praperadilan"] = context["fokus_praperadilan"]
            else:
                missing.append("tujuan_pembelaan_praperadilan")
                reasons.append("Mengetahui apakah user berniat menempuh jalur praperadilan untuk membatalkan penetapan status tersangkanya.")

            total_factors = 4
            known_factors = len(identified)
            score = round(known_factors / total_factors, 2)
            needs_clarification = score < 0.85

            return FactCompleteness(
                score=score,
                identified_elements=identified,
                missing_critical_elements=missing,
                needs_clarification=needs_clarification,
                clarification_reasons=reasons
            )

        # Default fallback untuk query umum
        return FactCompleteness(
            score=0.9,
            identified_elements={"query_type": "general_legal_inquiry"},
            missing_critical_elements=[],
            needs_clarification=False,
            clarification_reasons=[]
        )

    def generate_clarification_questions(
        self, query: str, completeness: FactCompleteness
    ) -> List[ClarificationQuestion]:
        """Generates proactive, tailored clarification questions with legal implications."""
        questions: List[ClarificationQuestion] = []
        missing = set(completeness.missing_critical_elements)

        if "unsur_perencanaan" in missing:
            questions.append(
                ClarificationQuestion(
                    id="q_perencanaan",
                    question="Apakah tindakan pembunuhan tersebut direncanakan terlebih dahulu atau terjadi secara spontan?",
                    context_why_needed=(
                        "Hukum pidana Indonesia membedakan secara tegas antara pembunuhan spontan (Pasal 338 KUHP, maksimal 15 tahun penjara) "
                        "dan pembunuhan berencana (Pasal 340 KUHP / Pasal 459 UU 1/2023, ancaman pidana mati atau penjara seumur hidup)."
                    ),
                    options=[
                        ClarificationOption(
                            label="Direncanakan (Ada persiapan / jeda waktu berpikir tenang)",
                            description="Pelaku telah mempersiapkan alat atau memiliki jeda waktu untuk mempertimbangkan akibat perbuatannya.",
                            legal_implication="Dapat dijerat Pasal 340 KUHP (KUHP Lama) atau Pasal 459 UU 1/2023 dengan ancaman pidana mati / seumur hidup."
                        ),
                        ClarificationOption(
                            label="Spontan / Emosi mendadak (Tanpa rencana sebelumnya)",
                            description="Peristiwa terjadi seketika akibat pertengkaran mendadak tanpa ada niat atau persiapan sebelumnya.",
                            legal_implication="Dikenakan pasal pembunuhan biasa (Pasal 338 KUHP / Pasal 458 UU 1/2023) dengan ancaman maksimal 15 tahun."
                        )
                    ]
                )
            )

        if "kondisi_kejiwaan_atau_daya_paksa" in missing:
            questions.append(
                ClarificationQuestion(
                    id="q_kejiwaan",
                    question="Apakah pelaku terindikasi memiliki gangguan kejiwaan atau berada dalam keadaan membela diri terpaksa?",
                    context_why_needed=(
                        "Pasal 44 KUHP mengatur bahwa orang yang jiwanya cacat dalam pertumbuhan atau terganggu penyakit tidak dapat dipidana (alasan pemaaf). "
                        "Sedangkan Pasal 49 KUHP menghapus pidana bagi tindakan pembelaan terpaksa (noodweer)."
                    ),
                    options=[
                        ClarificationOption(
                            label="Pelaku dalam kondisi sadar dan sehat akal",
                            description="Dapat dimintai pertanggungjawaban pidana penuh di muka pengadilan.",
                            legal_implication="Pertanggungjawaban pidana penuh berlaku."
                        ),
                        ClarificationOption(
                            label="Ada indikasi gangguan jiwa / depresi berat / perlu visum psikiatri",
                            description="Memerlukan pemeriksaan oleh dokter ahli jiwa (Visum et Repertum Psychiatricum).",
                            legal_implication="Jika terbukti menurut Pasal 44 KUHP, hakim dapat memerintahkan perawatan di RS jiwa dan tidak dijatuhi pidana penjara."
                        )
                    ]
                )
            )

        if "waktu_peristiwa_tempus" in missing:
            questions.append(
                ClarificationQuestion(
                    id="q_waktu_kejadian",
                    question="Kapan peristiwa tersebut terjadi (sebelum atau sesudah Januari 2026)?",
                    context_why_needed=(
                        "KUHP Nasional Baru (UU No. 1 Tahun 2023) mulai berlaku penuh per 2 Januari 2026 menggantikan KUHP lama peninggalan kolonial (WvS). "
                        "Berdasarkan asas Lex Favor Reo (Pasal 1 ayat 2 KUHP lama jo Pasal 3 UU 1/2023), jika ada perubahan peraturan, terdakwa berhak mendapatkan ketentuan yang paling meringankan."
                    ),
                    options=[
                        ClarificationOption(
                            label="Peristiwa terjadi sebelum 2 Januari 2026 (atau saat ini)",
                            description="Tunduk pada aturan KUHP lama (WvS / UU 1 Tahun 1946).",
                            legal_implication="Menggunakan pasal 338, 340, 356 ke-1 WvS."
                        ),
                        ClarificationOption(
                            label="Peristiwa terjadi setelah 2 Januari 2026",
                            description="Tunduk pada ketentuan KUHP Baru (UU No. 1 Tahun 2023).",
                            legal_implication="Menggunakan pasal 458, 459, dan pemberatan Pasal 58 huruf c UU 1/2023."
                        )
                    ]
                )
            )

        if "kecukupan_alat_bukti" in missing or "pemeriksaan_calon_tersangka" in missing:
            questions.append(
                ClarificationQuestion(
                    id="q_prosedur_tersangka",
                    question="Apakah calon tersangka sudah pernah diperiksa penyidik dan telah diperoleh minimal 2 alat bukti yang sah?",
                    context_why_needed=(
                        "Berdasarkan Putusan Mahkamah Konstitusi No. 21/PUU-XII/2014, penetapan status tersangka TANPA minimal 2 alat bukti sah "
                        "dan TANPA didahului pemeriksaan calon tersangkanya adalah CACAT HUKUM dan inkonstitusional."
                    ),
                    options=[
                        ClarificationOption(
                            label="Belum pernah diperiksa sama sekali, langsung ditetapkan sebagai tersangka",
                            description="Penyidik menetapkan status tersangka secara sepihak tanpa BAP saksi/calon tersangka.",
                            legal_implication="Pelanggaran prosedur mutlak! Sangat kuat untuk dibatalkan melalui gugatan Praperadilan di Pengadilan Negeri."
                        ),
                        ClarificationOption(
                            label="Sudah dipanggil dan diperiksa secara resmi sebagai saksi/calon tersangka",
                            description="Penyidik telah melakukan klarifikasi dan mengantongi bukti-bukti (surat, saksi, ahli).",
                            legal_implication="Prosedur formal terpenuhi, pengujian beralih ke materiil bukti dan dasar gelar perkara."
                        )
                    ]
                )
            )

        return questions
