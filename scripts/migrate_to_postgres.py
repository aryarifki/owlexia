"""Migrates seed data and crawled regulations into PostgreSQL (owlexia_db)."""
import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.database import OwlexiaDatabase
from seed_regulations import CORE_LEGAL_DATABASE


def migrate_all():
    db = OwlexiaDatabase()
    print("Testing connection to PostgreSQL...")
    if not db.test_connection():
        print("Error: Could not connect to PostgreSQL database!")
        return False

    print("PostgreSQL connection verified. Starting migration...")

    # 1. Group seed regulations by regulation slug
    reg_groups = {}
    for art in CORE_LEGAL_DATABASE:
        slug = art.regulation_number.lower().replace(" ", "-").replace("/", "-").replace(".", "")
        if "wvs" in slug or "1946" in slug:
            slug = "kuhp-wvs-1946"
            jenis = "Kitab Undang-Undang Hukum Pidana"
            nomor = "WvS"
            tahun = 1946
        elif "2023" in slug:
            slug = "uu-1-2023"
            jenis = "Undang-Undang"
            nomor = "1"
            tahun = 2023
        elif "1981" in slug:
            slug = "uu-8-1981"
            jenis = "Undang-Undang (KUHAP)"
            nomor = "8"
            tahun = 1981
        elif "putusan-mk" in slug or "21-puu" in slug:
            slug = "putusan-mk-21-2014"
            jenis = "Putusan Mahkamah Konstitusi"
            nomor = "21/PUU-XII/2014"
            tahun = 2014
        else:
            jenis = "Undang-Undang"
            nomor = str(art.regulation_year)
            tahun = art.regulation_year

        if slug not in reg_groups:
            reg_groups[slug] = {
                "peraturan_id_slug": slug,
                "jenis": jenis,
                "nomor": nomor,
                "tahun": tahun,
                "judul": art.regulation_name,
                "status": "BERLAKU",
                "articles": []
            }

        reg_groups[slug]["articles"].append({
            "article_number": art.article_number,
            "chapter": art.chapter,
            "part": art.notes,
            "content": art.content,
            "explanation": art.explanation,
            "category": "pidana_materiil" if "kuhp" in slug else ("pidana_formil" if "kuhap" in slug or "putusan" in slug else "umum"),
            "status": "BERLAKU",
            "keywords": [w.strip() for w in art.content.split()[:10]],
            "metadata": {"notes": art.notes}
        })

    # Upsert seed regulations and their articles
    total_articles_synced = 0
    for slug, reg_info in reg_groups.items():
        reg_id = db.upsert_regulation({
            "peraturan_id_slug": reg_info["peraturan_id_slug"],
            "jenis": reg_info["jenis"],
            "nomor": reg_info["nomor"],
            "tahun": reg_info["tahun"],
            "judul": reg_info["judul"],
            "status": reg_info["status"],
            "total_pasal": len(reg_info["articles"])
        })
        synced = db.upsert_articles_batch(reg_id, reg_info["articles"])
        total_articles_synced += synced
        print(f"Synced {synced} articles for regulation: {reg_info['judul']} ({slug})")

    # 2. Sync crawled parsed_regulations.json if available
    json_path = Path("/root/legal-ai-agent/data/parsed_regulations.json")
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                crawled_data = json.load(f)
            
            crawled_groups = {}
            for item in crawled_data:
                r_num = item.get("regulation_number", "UU 2026")
                slug = r_num.lower().replace(" ", "-").replace(".", "")
                if slug not in crawled_groups:
                    crawled_groups[slug] = {
                        "peraturan_id_slug": slug,
                        "jenis": "Undang-Undang",
                        "nomor": item.get("regulation_number", "5"),
                        "tahun": item.get("regulation_year", 2026),
                        "judul": item.get("regulation_name", "Peraturan Indonesia"),
                        "status": item.get("status", "BERLAKU"),
                        "articles": []
                    }
                crawled_groups[slug]["articles"].append({
                    "article_number": item.get("article_number", "1"),
                    "chapter": item.get("chapter"),
                    "part": None,
                    "content": item.get("content", ""),
                    "explanation": item.get("explanation"),
                    "status": item.get("status", "BERLAKU"),
                    "keywords": [],
                    "metadata": {"notes": item.get("notes")}
                })

            for slug, reg_info in crawled_groups.items():
                reg_id = db.upsert_regulation({
                    "peraturan_id_slug": reg_info["peraturan_id_slug"],
                    "jenis": reg_info["jenis"],
                    "nomor": reg_info["nomor"],
                    "tahun": reg_info["tahun"],
                    "judul": reg_info["judul"],
                    "status": reg_info["status"],
                    "total_pasal": len(reg_info["articles"])
                })
                synced = db.upsert_articles_batch(reg_id, reg_info["articles"])
                total_articles_synced += synced
                print(f"Synced {synced} crawled articles for: {reg_info['judul']}")
        except Exception as e:
            print(f"Warning: Failed to sync parsed_regulations.json: {e}")

    # 3. Insert landmark Putusan MK into court_decisions table
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO court_decisions (
                nomor_putusan, lembaga_peradilan, tahun, amar_putusan, kaidah_hukum, dampak_hukum, metadata
            ) VALUES (
                '21/PUU-XII/2014',
                'MK',
                2014,
                'Mengabulkan permohonan Pemohon untuk sebagian. Menyatakan Pasal 77 huruf a KUHAP inkonstitusional bersyarat sepanjang tidak dimaknai termasuk penetapan tersangka, penggeledahan, dan penyitaan.',
                'Penetapan tersangka adalah objek praperadilan. Syarat sah penetapan tersangka harus didasarkan minimal dua alat bukti sah (Pasal 184 KUHAP) serta pemeriksaan calon tersangka terlebih dahulu.',
                'Inkonstitusional Bersyarat (Mengikat Semua Aparat Penegak Hukum)',
                '{"pasal_terkait": ["Pasal 77 KUHAP", "Pasal 1 angka 14 KUHAP", "Pasal 184 KUHAP"]}'::jsonb
            ) ON CONFLICT (nomor_putusan) DO UPDATE SET
                amar_putusan = EXCLUDED.amar_putusan,
                kaidah_hukum = EXCLUDED.kaidah_hukum;
            """)
            conn.commit()
            print("Landmark Putusan MK 21/PUU-XII/2014 synced to court_decisions table.")

    total_in_db = db.get_total_articles_count()
    print(f"Total articles now in PostgreSQL (owlexia_db): {total_in_db}")
    return True


if __name__ == "__main__":
    migrate_all()
