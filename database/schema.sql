-- OWLEXIA: PostgreSQL Database Schema
-- Indonesian Legal Intelligence System (Peraturan.go.id, UU, KUHP, KUHAP, Putusan MK & MA)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Tabel Master Regulasi (Undang-Undang / Peraturan)
CREATE TABLE IF NOT EXISTS regulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peraturan_id_slug VARCHAR(120) UNIQUE NOT NULL,
    jenis VARCHAR(100) NOT NULL,                    -- e.g. "Undang-Undang", "Peraturan Pemerintah", "KUHP"
    nomor VARCHAR(50) NOT NULL,                     -- e.g. "1", "5", "WvS"
    tahun INTEGER NOT NULL,                         -- e.g. 2023, 2026, 1946
    judul TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'BERLAKU',  -- BERLAKU, DICABUT, DIUBAH, TIDAK_BERLAKU
    tanggal_pengundangan DATE,
    tanggal_berlaku DATE,
    instansi_pemrakarsa VARCHAR(255),
    sumber_url TEXT,                                -- URL detail peraturan.go.id
    pdf_path TEXT,                                  -- Path file PDF lokal
    total_pasal INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,             -- Menyimpan konsiderans menimbang, mengingat, riwayat status
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index Regulasi
CREATE INDEX IF NOT EXISTS idx_regulations_slug ON regulations(peraturan_id_slug);
CREATE INDEX IF NOT EXISTS idx_regulations_status ON regulations(status);
CREATE INDEX IF NOT EXISTS idx_regulations_tahun ON regulations(tahun);
CREATE INDEX IF NOT EXISTS idx_regulations_judul_trgm ON regulations USING gin(judul gin_trgm_ops);

-- 2. Tabel Norma & Pasal Hierarkis
CREATE TABLE IF NOT EXISTS legal_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regulation_id UUID REFERENCES regulations(id) ON DELETE CASCADE,
    article_number VARCHAR(80) NOT NULL,            -- e.g. "338", "340", "458", "77 ayat (1)"
    chapter VARCHAR(255),                           -- BAB
    part VARCHAR(255),                              -- BAGIAN / PARAGRAF
    content TEXT NOT NULL,                          -- Teks bunyi pasal lengkap
    explanation TEXT,                               -- Penjelasan resmi pasal demi pasal
    category VARCHAR(100),                          -- pidana_materiil, pidana_formil, tindak_pidana_khusus, etc.
    status VARCHAR(50) NOT NULL DEFAULT 'BERLAKU',  -- BERLAKU, DICABUT, DIAKTIFKAN_BERSYARAT
    keywords TEXT[] DEFAULT '{}',
    embedding vector(384),                          -- pgvector dense embedding
    metadata JSONB DEFAULT '{}'::jsonb,             -- rincian ayat, sanksi minimum/maksimum, denda
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(regulation_id, article_number)
);

-- Full-Text Search tsvector column (generated with Indonesian configuration)
ALTER TABLE legal_articles 
ADD COLUMN IF NOT EXISTS tsv_content tsvector 
GENERATED ALWAYS AS (
    to_tsvector('indonesian', coalesce(content, '') || ' ' || coalesce(explanation, '') || ' ' || coalesce(article_number, ''))
) STORED;

-- Index Pasal
CREATE INDEX IF NOT EXISTS idx_articles_reg_id ON legal_articles(regulation_id);
CREATE INDEX IF NOT EXISTS idx_articles_number ON legal_articles(article_number);
CREATE INDEX IF NOT EXISTS idx_articles_status ON legal_articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_tsv ON legal_articles USING gin(tsv_content);
CREATE INDEX IF NOT EXISTS idx_articles_content_trgm ON legal_articles USING gin(content gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_articles_metadata ON legal_articles USING gin(metadata);

-- 3. Tabel Putusan Pengadilan (Roadmap Mahkamah Konstitusi & Mahkamah Agung)
CREATE TABLE IF NOT EXISTS court_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nomor_putusan VARCHAR(120) UNIQUE NOT NULL,     -- e.g. "21/PUU-XII/2014"
    lembaga_peradilan VARCHAR(50) NOT NULL,         -- MK, MA
    tahun INTEGER NOT NULL,
    amar_putusan TEXT NOT NULL,
    kaidah_hukum TEXT NOT NULL,                     -- Ratio decidendi / doktrin hukum mengikat
    dampak_hukum VARCHAR(100),                      -- Inkonstitusional Bersyarat, Mengikat, etc.
    pdf_path TEXT,
    sumber_url TEXT,
    embedding vector(384),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabel Relasi Anotasi Putusan Peradilan terhadap Pasal UU
CREATE TABLE IF NOT EXISTS article_court_rulings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES legal_articles(id) ON DELETE CASCADE,
    court_decision_id UUID REFERENCES court_decisions(id) ON DELETE CASCADE,
    keterangan_dampak TEXT NOT NULL,                -- e.g. "Memperluas objek praperadilan termasuk penetapan tersangka"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(article_id, court_decision_id)
);

-- 5. Tabel Monitoring & Log Crawler Peraturan.go.id
CREATE TABLE IF NOT EXISTS crawler_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',  -- PENDING, DOWNLOADING, PARSED, INDEXED, FAILED
    total_articles INTEGER DEFAULT 0,
    file_path TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Trigger auto-update timestamp
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trg_update_regulations ON regulations;
CREATE TRIGGER trg_update_regulations
    BEFORE UPDATE ON regulations
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp_column();

DROP TRIGGER IF EXISTS trg_update_legal_articles ON legal_articles;
CREATE TRIGGER trg_update_legal_articles
    BEFORE UPDATE ON legal_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp_column();
