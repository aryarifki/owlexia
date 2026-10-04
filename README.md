# 🦉 OWLEXIA — Indonesian Legal AI Agent

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Domain](https://img.shields.io/badge/domain-owlexia.cugarete.me-blue.svg)](https://owlexia.cugarete.me)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%2B%20pgvector-336791.svg)]()
[![Cloudflare R2](https://img.shields.io/badge/Cloudflare_R2-Object_Storage-F38020.svg)]()
[![Gemini LLM](https://img.shields.io/badge/Gemini_LLM-Reasoning_Engine-4285F4.svg)]()
[![Tests](https://img.shields.io/badge/tests-26%2F26%20passed-brightgreen.svg)]()

**OWLEXIA** adalah platform asisten kecerdasan buatan hukum Indonesia berbasis data regulasi resmi ([peraturan.go.id](https://peraturan.go.id)), **Hierarchical Hybrid RAG**, dan **Proactive Reasoning Engine**.

OWLEXIA memadukan ketajaman analisis yuridis (metode IRAC — *Issue, Rule, Application, Conclusion*) dengan antarmuka modern bernuansa **Material 3 Expressive** dan filosofi **Anti-AI-Slop** dari *Hallmark Design*.

---

## 🌐 Akses Publik & Antarmuka

- **URL Produksi**: [https://owlexia.cugarete.me](https://owlexia.cugarete.me)
- **API Health**: `https://owlexia.cugarete.me/api/health`
- **Swagger Documentation**: `https://owlexia.cugarete.me/docs`
- **Routing**: Cloudflare Tunnel (Tunnel ID: `774c1dad-f104-457d-81cd-08c878bfbd4f`)

---

## 🏛️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph Client["Frontend (Material 3 Expressive)"]
        UI["React 18 + Tailwind CSS + Lucide Icons"]
    end

    subgraph Edge["Cloudflare Edge Network"]
        CF["Cloudflare Tunnel (owlexia.cugarete.me)"]
        R2["Cloudflare R2 (owlexia-r2 CDN Storage)"]
    end

    subgraph Service["Application Core (systemd: owlexia.service)"]
        API["FastAPI (Multi-Worker Uvicorn + GZipMiddleware)"]
        PM["PromptManager (Hot-reloading prompts/system_prompt.md)"]
        RE["LegalReasoner (IRAC Engine)"]
        LLM["Google Gemini API (Multi-Model Failover)"]
        HR["LegalRetriever (Hybrid BM25 + PostgreSQL FTS)"]
    end

    subgraph Storage["Knowledge Base (PostgreSQL 17)"]
        DB[("owlexia_db\n- regulations\n- legal_articles\n- crawler_sync_logs")]
        FTS["Indonesian Full-Text Search (GIN tsvector)"]
        VEC["pgvector Semantic Embeddings"]
    end

    subgraph Ingestion["Crawler Engine (O-Crawler)"]
        Crawler["anti_waf_crawler.py (Anti-WAF TLS/JA3 + R2 Upload)"]
    end

    UI <--> Edge
    Edge <--> API
    API <--> PM
    API <--> RE
    RE <--> LLM
    RE <--> HR
    HR <--> Storage
    Storage <--> R2
    Crawler --> Storage
    Crawler --> R2
```

---

## ✨ Fitur Unggulan

### 1. Dualisme Hukum Pidana & Asas *Lex Favor Reo*
- Mengakomodasi **KUHP Lama (WvS / UU 1/1946)** dan **KUHP Baru (UU No. 1 Tahun 2023)** yang berlaku per 2 Januari 2026.
- Menghitung pemberatan 1/3 (korban orang tua kandung, Pasal 58 c UU 1/2023 / Pasal 356 ke-1 KUHP lama) dan perbarengan tindak pidana (*Concursus Realis* Pasal 65 KUHP).

### 2. Sinergi Putusan MK & KUHAP
- Validasi penetapan tersangka sesuai **Putusan MK No. 21/PUU-XII/2014** (wajib minimal 2 alat bukti sah dan pemeriksaan calon tersangka) serta mekanisme hak Praperadilan.

### 3. Mesin Penalaran IRAC Berbasis Gemini LLM & Heuristik Deterministik
- **Gemini LLM Integration**: Penalaran mendalam menggunakan model Gemini (`gemini-flash-lite-latest` / `gemini-3.5-flash`) dengan skema JSON terstruktur.
- **Failover Bertingkat**: Otomatis berpindah model jika terjadi keterbatasan kuota atau timeout API, hingga ke penalaran heuristik rule-based jika jaringan offline.
- Output terstruktur mencakup: *Case Summary*, *Legal Issue*, *Application Analysis*, *Conclusion*, *Aggravating Factors*, *Mitigating Factors*, dan *Procedural Steps*.

### 4. Hybrid Retrieval (BM25 + PostgreSQL FTS Boost)
- Menggabungkan algoritma **BM25Okapi** pada korpus in-memory dengan **PostgreSQL Full-Text Search (FTS)** berbasis kamus bahasa Indonesia dan GIN index.
- Menjamin pasal-pasal baru yang di-*ingest* langsung dapat ditemukan seketika (*instant discoverability*).

### 5. Integrasi Cloudflare R2 Storage
- Dokumen PDF otentik lembaran negara disimpan di **Cloudflare R2 Object Storage** dengan zero egress cost.
- Tautan PDF resmi langsung tersaji pada kartu referensi pasal di frontend UI.

### 6. Dynamic Prompt System & Hot-Reloading
- System prompt disimpan pada file transparan [`prompts/system_prompt.md`](prompts/system_prompt.md).
- Dilengkapi **auto hot-reload** berbasis timestamp file (`mtime`). Modifikasi prompt langsung aktif saat runtime tanpa memerlukan restart server.
- Tersedia endpoint `GET /api/prompt` dan `POST /api/prompt` untuk pembaruan prompt terprogram.

### 7. Optimasi Kinerja Kelas Produksi
- **GZip Compression**: Kompresi respon otomatis (`GZipMiddleware(minimum_size=1000)`).
- **Multi-Worker Execution**: Menjalankan 2 worker proses Uvicorn konkuren.
- **Daemon Otomatis**: Dikelola oleh systemd (`owlexia.service`) dengan *auto-restart on failure*.

---

## 📂 Struktur Proyek

```
/root/legal-ai-agent/
├── api.py                    # Server FastAPI utama & mounting frontend
├── cli.py                    # Terminal CLI interaktif & mode demo
├── pytest.ini                # Konfigurasi pengujian pytest
├── requirements.txt          # Dependensi Python
├── env.example               # Template konfigurasi environment
├── database/
│   └── schema.sql            # Skema DDL tabel PostgreSQL 17
├── engine/
│   ├── agent_system.py       # Orchestrator agen hukum utama
│   ├── config.py             # Manajemen konfigurasi terpusat & .env
│   ├── database.py           # Adapter PostgreSQL & full-text search
│   ├── models.py             # Model data Pydantic (LegalArticle, Assessment, dll.)
│   ├── parser.py             # Parser dokumen hukum & ekstraksi pasal
│   ├── proactive_agent.py    # Modul klarifikasi proaktif perkara hukum
│   ├── prompt_manager.py     # Engine hot-reload system prompt
│   ├── reasoner.py           # Engine penalaran yuridis IRAC (Gemini LLM + Heuristik)
│   └── retriever.py          # Hybrid retrieval (BM25 + SQL FTS Boost)
├── prompts/
│   ├── system_prompt.md      # SYSTEM PROMPT AKTIF (dapat diedit langsung)
│   └── README.md             # Panduan struktur penulisan prompt
├── scripts/
│   └── migrate_to_postgres.py# Skrip migrasi data lokal ke PostgreSQL
├── static/                   # Fallback web assets
├── tests/                    # 26 Unit tests lengkap
│   ├── test_api.py
│   ├── test_database.py
│   ├── test_gemini_reasoner.py
│   ├── test_legal_agent.py
│   ├── test_parser.py
│   └── test_prompt_manager.py
└── web/                      # Aplikasi Frontend (React 18 + Vite)
    ├── src/                  # Komponen React (Material 3 Expressive)
    ├── dist/                 # Build produksi yang disajikan oleh FastAPI
    └── package.json
```

---

## 🛠️ Panduan Instalasi & Penggunaan

### 1. Setup Lingkungan Python
```bash
git clone git@github.com:aryarifki/owlexia.git
cd owlexia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfigurasi Lingkungan (`.env`)
Salin file konfigurasi:
```bash
cp env.example .env
```
Sesuaikan parameter kredensial:
```env
DATABASE_URL=postgresql://owlexia:owlexia_pass@localhost:5432/owlexia_db
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
REASONER_MODE=llm
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_BUCKET_NAME=owlexia-r2
R2_API_TOKEN=your_r2_api_token
R2_PUBLIC_URL=https://pub-xxxxxx.r2.dev
```

### 3. Konfigurasi Database PostgreSQL
Inisialisasi skema tabel di PostgreSQL:
```bash
sudo -u postgres psql -d owlexia_db -f database/schema.sql
```

### 4. Menjalankan Server Lokal (Development)
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
Akses di browser: `http://localhost:8000`

---

## 🔧 Manajemen Layanan Produksi (Systemd)

Aplikasi OWLEXIA dikelola sebagai system service di Linux:

| Perintah | Deskripsi |
| :--- | :--- |
| `sudo systemctl status owlexia` | Memeriksa status berjalan layanan OWLEXIA |
| `sudo systemctl restart owlexia` | Memulai ulang layanan OWLEXIA |
| `sudo systemctl stop owlexia` | Menghentikan layanan OWLEXIA |
| `sudo journalctl -u owlexia -f -n 50` | Memantau log aplikasi secara real-time |

### File Konfigurasi Layanan: `/etc/systemd/system/owlexia.service`
```ini
[Unit]
Description=OWLEXIA Legal AI Agent Production Service
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/legal-ai-agent
EnvironmentFile=/root/legal-ai-agent/.env
Environment="PYTHONPATH=/root/legal-ai-agent"
ExecStart=/root/legal-ai-agent/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

---

## 🧪 Pengujian (Test Suite)

OWLEXIA dilengkapi 26 unit test otomatis yang mencakup pengujian API, konektivitas database PostgreSQL, logika penalaran IRAC berbasis Gemini LLM & fallback heuristik, klarifikasi proaktif, parser regulasi, dan hot-reloading prompt manager:

```bash
cd /root/legal-ai-agent
./venv/bin/pytest
```

**Hasil Pengujian:**
```
======================== 26 passed, 1 warning in 27.53s ========================
```

---

## 📄 Lisensi

MIT License © 2026 [Arya Rifki Pratama](https://github.com/aryarifki).
Dirancang & dikembangkan sebagai bagian dari ekosistem riset AI Agent.
