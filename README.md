# 🦉 OWLEXIA — Indonesian Legal AI Agent

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Domain](https://img.shields.io/badge/domain-owlexia.cugarete.me-blue.svg)](https://owlexia.cugarete.me)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%2B%20pgvector-336791.svg)]()
[![Tests](https://img.shields.io/badge/tests-24%2F24%20passed-brightgreen.svg)]()

**OWLEXIA** adalah platform asisten kecerdasan buatan hukum Indonesia berbasis data regulasi resmi ([peraturan.go.id](https://peraturan.go.id)), **Hierarchical Hybrid RAG**, dan **Proactive Reasoning Engine**.

OWLEXIA memadukan ketajaman analisis yuridis (metode IRAC — *Issue, Rule, Application, Conclusion*) dengan antarmuka modern bernuansa **Material 3 Expressive** dan filosofi **Anti-AI-Slop** dari *Hallmark Design*.

---

## 🌐 Akses Publik

- **URL Produksi**: [https://owlexia.cugarete.me](https://owlexia.cugarete.me)
- **API Health**: `https://owlexia.cugarete.me/api/health`
- **Swagger Documentation**: `https://owlexia.cugarete.me/docs`
- **Routing**: Cloudflare Tunnel (Tunnel ID: `774c1dad-f104-457d-81cd-08c878bfbd4f`)

---

## 🏛️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph Client["Frontend (Material 3 Expressive)"]
        UI["React 18 + Tailwind CSS + Lucide"]
    end

    subgraph Edge["Cloudflare Edge Network"]
        CF["Cloudflare Tunnel (owlexia.cugarete.me)"]
    end

    subgraph Service["Application Core (systemd: owlexia.service)"]
        API["FastAPI (Multi-Worker Uvicorn + GZipMiddleware)"]
        PM["PromptManager (Hot-reloading prompts/system_prompt.md)"]
        RE["Proactive Reasoning Engine (IRAC + Legal Dualism)"]
    end

    subgraph Storage["Knowledge Base (PostgreSQL 17)"]
        DB[("owlexia_db\n- regulations\n- legal_articles\n- crawler_sync_logs")]
        FTS["Indonesian Full-Text Search (GIN tsvector)"]
        VEC["pgvector Semantic Embeddings"]
    end

    subgraph Ingestion["Crawler Engine (/root/Peraturan-Crawler)"]
        Crawler["targeted_crawler.js (Targeted by Year & Keyword)"]
    end

    UI <--> Edge
    Edge <--> API
    API <--> PM
    API <--> RE
    RE <--> Storage
    Crawler --> Storage
```

---

## ✨ Fitur Unggulan

### 1. Dualisme Hukum Pidana & Asas *Lex Favor Reo*
- Mengakomodasi **KUHP Lama (WvS / UU 1/1946)** dan **KUHP Baru (UU No. 1 Tahun 2023)** yang berlaku per 2 Januari 2026.
- Menghitung pemberatan 1/3 (korban orang tua kandung, Pasal 58 c UU 1/2023 / Pasal 356 ke-1 KUHP lama) dan perbarengan tindak pidana (*Concursus Realis* Pasal 65 KUHP).

### 2. Sinergi Putusan MK & KUHAP
- Validasi penetapan tersangka sesuai **Putusan MK No. 21/PUU-XII/2014** (wajib minimal 2 alat bukti sah dan pemeriksaan calon tersangka) serta mekanisme hak Praperadilan.

### 3. Dynamic Prompt System & Hot-Reloading
- System prompt disimpan pada file transparan [`prompts/system_prompt.md`](prompts/system_prompt.md).
- Dilengkapi **auto hot-reload** berbasis timestamp file (`mtime`). Modifikasi prompt langsung aktif saat runtime tanpa memerlukan restart server.
- Tersedia endpoint `GET /api/prompt` dan `POST /api/prompt` untuk melihat dan memperbarui prompt secara terprogram.

### 4. Natural & Conversational Intelligence
- Agen menjawab pertanyaan umum (katalog peraturan, status regulasi, penjelasan konsep) dengan ramah, komunikatif, dan berbasis data tanpa memuntahkan pasal-pasal mentah jika tidak diminta.

### 5. Optimasi Kinerja Kelas Produksi (InvestOwl Reference)
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
├── env.example               # Contoh konfigurasi environment
├── database/
│   └── schema.sql            # Skema DDL tabel PostgreSQL 17
├── engine/
│   ├── agent_system.py       # Orchestrator agen hukum
│   ├── database.py           # PostgreSQL adapter & full-text search
│   ├── models.py             # Schema Pydantic
│   ├── parser.py             # Parser dokumen hukum & ekstraksi pasal
│   ├── proactive_agent.py    # Klarifikasi proaktif kasus hukum
│   ├── prompt_manager.py     # Engine hot-reload system prompt
│   ├── reasoner.py           # Engine penalaran yuridis IRAC
│   └── retriever.py          # Hybrid retrieval (BM25 + SQL FTS)
├── prompts/
│   ├── system_prompt.md      # SYSTEM PROMPT AKTIF (dapat diedit langsung)
│   └── README.md             # Panduan struktur penulisan prompt
├── scripts/
│   └── migrate_to_postgres.py# Skrip migrasi data lokal ke PostgreSQL
├── static/                   # Fallback web assets
├── tests/                    # 24 Unit tests lengkap
│   ├── test_api.py
│   ├── test_database.py
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
cd /root/legal-ai-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfigurasi Database PostgreSQL
Pastikan database `owlexia_db` telah dibuat di PostgreSQL:
```bash
# Jalankan skema DDL
sudo -u postgres psql -d owlexia_db -f database/schema.sql
```

### 3. Migrasi & Seeding Data Awal (Opsional)
```bash
python scripts/migrate_to_postgres.py
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
Environment="DATABASE_URL=postgresql://owlexia:owlexia_pass@localhost:5432/owlexia_db"
ExecStart=/root/legal-ai-agent/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

---

## 🌐 Pemeliharaan Cloudflare Tunnel

Subdomain `https://owlexia.cugarete.me` terhubung melalui tunnel `investowl-tunnel` (`774c1dad-f104-457d-81cd-08c878bfbd4f`).

- Konfigurasi rute berada di: `/etc/cloudflared/config.yml`
- Status Tunnel:
  ```bash
  sudo systemctl status cloudflared
  ```
- Restart Tunnel jika diperlukan:
  ```bash
  sudo systemctl restart cloudflared
  ```

---

## 🗃️ Prosedur Pencadangan Database (Backup & Restore)

### Backup Database:
```bash
pg_dump -U owlexia -h localhost -d owlexia_db -F c -b -v -f /root/owlexia_db_backup_$(date +%Y%m%d).dump
```

### Restore Database:
```bash
pg_restore -U owlexia -h localhost -d owlexia_db -v /root/owlexia_db_backup_YYYYMMDD.dump
```

---

## 🧪 Pengujian (Test Suite)

OWLEXIA dilengkapi 24 unit test yang mencakup pengujian API, konektivitas database PostgreSQL, logika penalaran IRAC, klarifikasi proaktif, parser regulasi, dan hot-reloading prompt manager:

```bash
cd /root/legal-ai-agent
/root/legal-ai-agent/venv/bin/pytest
```

**Hasil Pengujian:**
```
======================== 24 passed, 1 warning in 0.96s =========================
```

---

## 📄 Lisensi

MIT License © 2026 [Arya Rifki Pratama](https://github.com/aryarifki).
Dirancang & dikembangkan sebagai bagian dari ekosistem riset AI Agent.
