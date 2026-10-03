# 📜 Panduan Kustomisasi System Prompt OWLEXIA

Direktori ini berisi seluruh berkas prompt yang mengontrol identitas, kepribadian, gaya bahasa, dan logika penalaran agen AI hukum **OWLEXIA**.

---

## 📁 Berkas Prompt yang Tersedia

1. **[`system_prompt.md`](./system_prompt.md)** (Utama):
   - Mengatur identitas agen (*Identity*), kepribadian, nada bicara (*Tone & Registers*), dan batasan etika hukum (*Disclaimer*).
   - Mengatur kapan agen harus berbicara ramah/santai vs kapan harus melakukan analisis hukum formal (IRAC).
2. **[`clarification_rules.md`](./clarification_rules.md)**:
   - Mengatur kapan agen harus menghentikan kesimpulan dan mengajukan pertanyaan klarifikasi proaktif kepada pengguna.

---

## ⚡ Fitur Hot-Reload (Otomatis Diperbarui)

Aplikasi OWLEXIA dilengkapi dengan modul `PromptManager` yang memonitor *timestamp* berkas secara otomatis:
- **Anda tidak perlu me-restart server setiap kali mengedit berkas `.md` ini.**
- Begitu Anda menyimpan perubahan di `prompts/system_prompt.md`, kueri berikutnya yang diajukan oleh pengguna akan langsung menggunakan prompt terbaru!

---

## 🛠️ Cara Mengedit Prompt

### Cara 1: Mengedit Langsung Lewat Terminal
Gunakan teks editor favorit Anda di terminal (misal: `nano`, `vim`, atau VS Code / Antigravity IDE):
```bash
nano /root/legal-ai-agent/prompts/system_prompt.md
```

### Cara 2: Memeriksa Prompt Lewat API
Anda dapat melihat prompt aktif saat ini melalui API:
```bash
curl http://localhost:8000/api/prompt
```
Atau memperbaruinya melalui API:
```bash
curl -X POST http://localhost:8000/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt_content": "# Prompt baru..."}'
```

---

## 💡 Tips Prompt Engineering untuk OWLEXIA

- **Gunakan Tag XML** seperti `<identity>`, `<tone_and_registers>`, `<rules>`: Model LLM mematuhi instruksi dalam tag XML dengan konsistensi yang jauh lebih tinggi.
- **Jaga Efisiensi Token**: Pertahankan ukuran system prompt antara 500 – 1.500 token agar latensi respons tetap cepat di bawah 1-2 detik.
