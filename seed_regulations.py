"""Koleksi Data Awal Regulasi Hukum Indonesia untuk RAG Engine.

Mencakup:
1. KUHP Lama (Wetboek van Strafrecht / UU 1/1946)
2. KUHP Baru (UU No. 1 Tahun 2023)
3. KUHAP (UU No. 8 Tahun 1981)
4. Putusan Mahkamah Konstitusi No. 21/PUU-XII/2014
"""
from typing import List
from engine.models import LegalArticle, LegalHierarchyLevel, RegulationStatus

CORE_LEGAL_DATABASE: List[LegalArticle] = [
    # --- KUHP LAMA (WvS) ---
    LegalArticle(
        id="kuhp-lama-338",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Lama)",
        regulation_number="WvS / UU 1 Tahun 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XIX: Kejahatan Terhadap Nyawa",
        article_number="338",
        content=(
            "Barang siapa dengan sengaja merampas nyawa orang lain, diancam karena pembunuhan "
            "dengan pidana penjara paling lama lima belas tahun."
        ),
        explanation="Mengatur delik pembunuhan biasa (doodslag) tanpa rencana terlebih dahulu.",
        notes="Berlaku sampai dengan 1 Januari 2026 atau diterapkan jika perbuatan terjadi sebelum 2 Januari 2026."
    ),
    LegalArticle(
        id="kuhp-lama-340",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Lama)",
        regulation_number="WvS / UU 1 Tahun 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XIX: Kejahatan Terhadap Nyawa",
        article_number="340",
        content=(
            "Barang siapa dengan sengaja dan dengan rencana lebih dahulu merampas nyawa orang lain, "
            "diancam karena pembunuhan dengan rencana (moord), dengan pidana mati atau pidana penjara seumur hidup "
            "atau selama waktu tertentu, paling lama dua puluh tahun."
        ),
        explanation=(
            "Unsur penting: 1) dengan sengaja; 2) dengan rencana terlebih dahulu (ada jeda waktu untuk berpikir tenang); "
            "3) merampas nyawa orang lain. Sering didakwakan pada pembunuhan satu keluarga atau pembunuhan berencana."
        ),
        notes="Sanksi maksimal: Pidana Mati atau Penjara Seumur Hidup."
    ),
    LegalArticle(
        id="kuhp-lama-356",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Lama)",
        regulation_number="WvS / UU 1 Tahun 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XX: Penganiayaan",
        article_number="356 ke-1",
        content=(
            "Pidana yang ditentukan dalam pasal 351, 353, 354, dan 355 dapat ditambah dengan sepertiga: "
            "ke-1. bagi yang melakukan kejahatan itu terhadap ibunya, bapaknya yang sah, istrinya atau anaknya."
        ),
        explanation=(
            "Ketentuan pemberatan pidana sebesar 1/3 jika tindak pidana kekerasan/penganiayaan dilakukan terhadap orang tua kandung/sah."
        ),
        notes="Unsur pemberat hubungan keluarga sedarah garis lurus ke atas."
    ),
    LegalArticle(
        id="kuhp-lama-65",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Lama)",
        regulation_number="WvS / UU 1 Tahun 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB VI: Perbarengan Tindak Pidana (Concursus)",
        article_number="65",
        content=(
            "(1) Dalam hal perbarengan beberapa perbuatan yang harus dipandang sebagai perbuatan yang berdiri sendiri "
            "sehingga merupakan beberapa kejahatan, yang diancam dengan pidana pokok yang sejenis, maka dijatuhkan hanya satu pidana. "
            "(2) Maksimum pidana yang dijatuhkan ialah jumlah maksimum pidana yang diancamkan terhadap perbuatan itu, "
            "tetapi boleh lebih dari maksimum pidana yang terberat ditambah sepertiga."
        ),
        explanation=(
            "Concursus Realis: Menjawab kasus pembunuhan beberapa korban (misal: satu keluarga). Jika diancam dengan pidana mati "
            "atau seumur hidup, maka pidana pokok terberat (seumur hidup/mati) yang dijatuhkan menyerap pidana lainnya."
        ),
        notes="Prinsip absorbsi dipertajam jika ada ancaman pidana seumur hidup atau mati."
    ),
    LegalArticle(
        id="kuhp-lama-44",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Lama)",
        regulation_number="WvS / UU 1 Tahun 1946",
        regulation_year=1946,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB III: Hal-Hal yang Menghapuskan, Mengurangi, atau Memberatkan Pidana",
        article_number="44",
        content=(
            "(1) Tiada dapat dipidana barangsiapa melakukan perbuatan yang tidak dapat dipertanggungjawabkan kepadanya "
            "disebabkan karena jiwanya cacat dalam tumbuhnya atau terganggu karena penyakit."
        ),
        explanation="Alasan pemaaf: Menghapuskan kesalahan terdakwa akibat gangguan kejiwaan/psikologis.",
        notes="Diuji melalui pemeriksaan psikiatri forensik (visum et repertum psychiatricum)."
    ),

    # --- KUHP BARU (UU NO. 1 TAHUN 2023) ---
    LegalArticle(
        id="uu-1-2023-458",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Baru)",
        regulation_number="UU No. 1 Tahun 2023",
        regulation_year=2023,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XXI: Tindak Pidana Terhadap Tubuh dan Nyawa",
        article_number="458",
        content=(
            "(1) Setiap Orang yang merampas nyawa orang lain, dipidana karena pembunuhan, dengan pidana penjara paling lama 15 (lima belas) tahun. "
            "(2) Pembunuhan yang didahului, disertai, atau diikuti dengan Tindak Pidana lain dipidana dengan pidana penjara paling lama 20 (dua puluh) tahun."
        ),
        explanation="Setara dengan Pasal 338 dan 339 KUHP lama.",
        effective_date="2026-01-02",
        notes="Mulai berlaku efektif 2 Januari 2026."
    ),
    LegalArticle(
        id="uu-1-2023-459",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Baru)",
        regulation_number="UU No. 1 Tahun 2023",
        regulation_year=2023,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XXI: Tindak Pidana Terhadap Tubuh dan Nyawa",
        article_number="459",
        content=(
            "Setiap Orang yang dengan rencana terlebih dahulu merampas nyawa orang lain, dipidana karena pembunuhan berencana, "
            "dengan pidana mati atau pidana penjara seumur hidup atau pidana penjara paling lama 20 (dua puluh) tahun."
        ),
        explanation="Padanan Pasal 340 KUHP lama.",
        effective_date="2026-01-02",
        notes="Dalam UU 1/2023, pidana mati diatur sebagai pidana alternatif dengan masa percobaan 10 tahun (Pasal 100)."
    ),
    LegalArticle(
        id="uu-1-2023-58",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Baru)",
        regulation_number="UU No. 1 Tahun 2023",
        regulation_year=2023,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB II: Pidana dan Pemidanaan",
        article_number="58 huruf c",
        content=(
            "Pidana dapat ditambah 1/3 (satu pertiga) dari batas maksimum ancaman pidana jika tindak pidana dilakukan: "
            "c. terhadap ayah, ibu, anak, suami, atau istri dari pelaku."
        ),
        explanation=(
            "Ketentuan umum pemberatan sanksi pidana 1/3 jika korban merupakan keluarga sedarah garis lurus (ayah atau ibu kandung)."
        ),
        effective_date="2026-01-02",
        notes="Secara tegas menaikkan batas hukuman jika korban adalah orang tua kandung."
    ),
    LegalArticle(
        id="uu-1-2023-3",
        regulation_name="Kitab Undang-Undang Hukum Pidana (KUHP Baru)",
        regulation_number="UU No. 1 Tahun 2023",
        regulation_year=2023,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB I: Ruang Lingkup Berlakunya Hukum Pidana",
        article_number="3",
        content=(
            "(1) Dalam hal terdapat perubahan peraturan perundang-undangan sesudah perbuatan terjadi, diberlakukan peraturan yang baru, "
            "kecuali peraturan yang lama lebih menguntungkan bagi pelaku dan pembantu Tindak Pidana. "
            "(2) Dalam hal perbuatan yang terjadi tidak lagi merupakan Tindak Pidana menurut peraturan perundang-undangan yang baru, "
            "tuntutan pidana terhadap pelaku dan pembantu Tindak Pidana dihapuskan."
        ),
        explanation="Asas Lex Favor Reo: Menjamin penerapan aturan yang paling meringankan bagi terdakwa dalam masa transisi hukum.",
        effective_date="2026-01-02"
    ),

    # --- HUKUM ACARA PIDANA (KUHAP - UU NO. 8 TAHUN 1981) ---
    LegalArticle(
        id="kuhap-1-angka-14",
        regulation_name="Kitab Undang-Undang Hukum Acara Pidana (KUHAP)",
        regulation_number="UU No. 8 Tahun 1981",
        regulation_year=1981,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.DIUJI_MK,
        chapter="BAB I: Ketentuan Umum",
        article_number="1 angka 14",
        content=(
            "Tersangka adalah seorang yang karena perbuatannya atau keadaannya, berdasarkan bukti permulaan "
            "patut diduga sebagai pelaku tindak pidana."
        ),
        explanation=(
            "Norma tekstual awal KUHAP. Telah diuji dan dimaknai secara inkonstitusional bersyarat oleh Mahkamah Konstitusi "
            "melalui Putusan No. 21/PUU-XII/2014."
        ),
        notes="Wajib dibaca bersama Putusan Mahkamah Konstitusi No. 21/PUU-XII/2014!"
    ),
    LegalArticle(
        id="kuhap-184",
        regulation_name="Kitab Undang-Undang Hukum Acara Pidana (KUHAP)",
        regulation_number="UU No. 8 Tahun 1981",
        regulation_year=1981,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.BERLAKU,
        chapter="BAB XVI: Pembuktian",
        article_number="184 ayat (1)",
        content=(
            "Alat bukti yang sah ialah: a. keterangan saksi; b. keterangan ahli; c. surat; d. petunjuk; e. keterangan terdakwa."
        ),
        explanation=(
            "Daftar limitatif alat bukti yang sah dalam proses pidana Indonesia. Untuk menetapkan tersangka, penyidik wajib "
            "memiliki minimal 2 (dua) alat bukti yang sah."
        ),
        notes="Minimal dua alat bukti sah mutlak diperlukan untuk penetapan status tersangka."
    ),
    LegalArticle(
        id="kuhap-109",
        regulation_name="Kitab Undang-Undang Hukum Acara Pidana (KUHAP)",
        regulation_number="UU No. 8 Tahun 1981",
        regulation_year=1981,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.DIUJI_MK,
        chapter="BAB XIV: Penyidikan",
        article_number="109 ayat (1)",
        content=(
            "Dalam hal penyidik telah mulai melakukan penyidikan suatu peristiwa yang merupakan tindak pidana, "
            "penyidik memberitahukan hal itu kepada penuntut umum (SPDP)."
        ),
        explanation=(
            "Mewajibkan Surat Pemberitahuan Dimulainya Penyidikan (SPDP). Putusan MK No. 130/PUU-XIII/2015 mewajibkan SPDP "
            "dikirimkan kepada penuntut umum, terlapor, dan korban paling lambat 7 hari setelah terbit Sprindik."
        ),
        notes="Kewajiban penyampaian SPDP kepada terlapor/calon tersangka."
    ),
    LegalArticle(
        id="kuhap-77",
        regulation_name="Kitab Undang-Undang Hukum Acara Pidana (KUHAP)",
        regulation_number="UU No. 8 Tahun 1981",
        regulation_year=1981,
        hierarchy_level=LegalHierarchyLevel.UU_PERPPU,
        status=RegulationStatus.DIUJI_MK,
        chapter="BAB X: Wewenang Pengadilan untuk Mengadili - Bagian Kesatu: Praperadilan",
        article_number="77 huruf a",
        content=(
            "Pengadilan negeri berwenang untuk memeriksa dan memutus, sesuai dengan ketentuan yang diatur dalam undang-undang ini tentang: "
            "a. sah atau tidaknya penangkapan, penahanan, penghentian penyidikan atau penghentian penuntutan."
        ),
        explanation=(
            "Diperluas secara mengikat oleh Putusan MK 21/PUU-XII/2014, sehingga penetapan tersangka, penggeledahan, dan penyitaan "
            "sah menjadi objek Praperadilan."
        ),
        notes="Pintu hukum bagi seseorang untuk menggugat keabsahan penetapan status tersangkanya."
    ),

    # --- PUTUSAN MAHKAMAH KONSTITUSI RI ---
    LegalArticle(
        id="putusan-mk-21-2014",
        regulation_name="Putusan Mahkamah Konstitusi RI",
        regulation_number="Nomor 21/PUU-XII/2014",
        regulation_year=2014,
        hierarchy_level=LegalHierarchyLevel.PUTUSAN_MK,
        status=RegulationStatus.BERLAKU,
        chapter="Uji Materiil KUHAP Terhadap UUD 1945",
        article_number="Amar Putusan MK No. 21/PUU-XII/2014",
        content=(
            "1. Menyatakan frasa 'bukti permulaan', 'bukti permulaan yang cukup', dan 'bukti yang cukup' dalam Pasal 1 angka 14, "
            "Pasal 17, dan Pasal 21 ayat (1) KUHAP adalah inkonstitusional bersyarat sepanjang tidak dimaknai sebagai 'minimal dua alat bukti yang sah' "
            "sebagaimana diatur dalam Pasal 184 KUHAP dan disertai pemeriksaan calon tersangkanya.\n"
            "2. Menyatakan Pasal 77 huruf a KUHAP inkonstitusional bersyarat sepanjang tidak dimaknai termasuk penetapan tersangka, penggeledahan, dan penyitaan."
        ),
        explanation=(
            "YURISPRUDENSI FUNDAMENTAL: Polisi TIDAK BOLEH menetapkan seseorang sebagai tersangka secara sepihak tanpa: "
            "1) Minimal 2 alat bukti sah; 2) Pemeriksaan terhadap calon tersangka terlebih dahulu. "
            "Jika dilanggar, penetapan tersangka dapat dibatalkan melalui gugatan Praperadilan."
        ),
        notes="Putusan MK bersifat final and binding (mengikat seluruh aparat penegak hukum di Indonesia)."
    )
]


def get_all_articles() -> List[LegalArticle]:
    return CORE_LEGAL_DATABASE
