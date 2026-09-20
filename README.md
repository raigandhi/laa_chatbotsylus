# 💠 Sylus Chatbot — Roleplay NPC dari *Love and Deepspace*

Chatbot berbasis LLM (via **Groq API**) yang berperan sebagai **Sylus**, salah satu karakter
di game otome *Love and Deepspace*. Chatbot ini bisa diajak ngobrol santai, curhat, atau
sekadar say hi — dengan kepribadian yang karismatik, sedikit misterius, tapi hangat dan
suportif, sesuai karakter aslinya.

Chatbot tersedia dalam dua bentuk:
- **Console/terminal** (`chatbot_console.py`) — bisa dijalankan di terminal lokal, Jupyter
  Notebook, maupun Google Colab.
- **Web app** (`streamlit_app.py`) — antarmuka chat interaktif berbasis Streamlit, dengan
  jawaban yang muncul secara *streaming*.

## 1. Konsep Tema

Sylus digambarkan sebagai sosok yang percaya diri dan penuh kendali, namun selalu punya sisi
hangat untuk orang yang ia percaya. System prompt chatbot ini dirancang agar:
- Nada bicara tetap konsisten dengan karakter asli (karismatik, sedikit menggoda tapi elegan,
  suportif).
- Ada batasan tegas terhadap konten dewasa/eksplisit, kekerasan, ujaran kebencian, dan topik
  yang melanggar kebijakan penggunaan AI — semua diatur langsung di system prompt
  (lihat `SYSTEM_PROMPT` di `utils.py`).
- Saat pengguna curhat tentang hal berat, Sylus tetap suportif tapi juga mengarahkan pengguna
  untuk berbicara dengan orang tepercaya/profesional, bukan berpura-pura jadi pengganti bantuan
  profesional.

## 2. Struktur Kode

```
sylus-chatbot/
├── chatbot_console.py   # Loop chatbot untuk terminal/console
├── streamlit_app.py     # Aplikasi web (Streamlit)
├── utils.py             # Logika inti bersama: API key, system prompt, streaming,
│                         #   simpan/muat riwayat, statistik
├── .env.example          # Contoh file environment variable
├── .gitignore             # Memastikan .env & riwayat chat tidak ter-commit
├── requirements.txt       # Daftar dependensi Python
└── README.md              # Dokumentasi ini
```

**Penjelasan singkat tiap file:**

| File | Fungsi |
|---|---|
| `utils.py` | Berisi `load_api_key()` & `get_client()` (memuat API key dari `.env`/env var/Colab Secrets), `SYSTEM_PROMPT` persona Sylus, `reset_history()`, `stream_response()` (generator streaming ke Groq API), `save_history()` / `load_history()` (JSON), serta `compute_stats()` / `format_stats()` untuk statistik percakapan. |
| `chatbot_console.py` | Loop `while True` untuk chat di terminal. Menangani perintah `exit`/`keluar`, `clear`/`reset`, `save`, `load <file>`, `stats`, `help`, dan menangkap error API tanpa membuat program crash. |
| `streamlit_app.py` | UI web: chat bubble dengan `st.chat_message`, streaming jawaban lewat placeholder yang di-update, sidebar berisi slider `temperature`/`max_tokens`, tombol reset & simpan, upload untuk memuat riwayat, dan panel statistik live. |

## 3. Cara Menjalankan

### a. Instalasi

```bash
# (opsional tapi disarankan) buat virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### b. Setup API Key

Dapatkan API key gratis di [console.groq.com/keys](https://console.groq.com/keys), lalu pilih
salah satu cara berikut:

**Opsi 1 — File `.env` (untuk terminal lokal):**
```bash
cp .env.example .env
# lalu edit .env dan isi GROQ_API_KEY=isi_api_key_kamu
```

**Opsi 2 — Environment variable langsung:**
```bash
export GROQ_API_KEY="isi_api_key_kamu"      # Windows (PowerShell): $env:GROQ_API_KEY="..."
```

**Opsi 3 — Google Colab Secrets:**
1. Klik ikon 🔑 di sidebar kiri Colab → **Add new secret**
2. Nama: `GROQ_API_KEY`, isi dengan API key kamu, aktifkan **Notebook access**

Jika tidak ada satupun yang di-set, program akan meminta kamu mengetik API key secara manual
(tersembunyi, lewat `getpass`) — jadi program tidak akan pernah crash hanya karena key belum
di-setup.

> ⚠️ **Jangan pernah** menaruh API key langsung di dalam kode atau meng-commit file `.env` ke
> repository. File `.gitignore` di sini sudah menyertakan `.env` agar aman.

### c. Menjalankan versi Console

```bash
python chatbot_console.py
```

Di Jupyter Notebook / Google Colab, upload semua file lalu jalankan:
```python
%run chatbot_console.py
```

### d. Menjalankan versi Web (Streamlit)

```bash
streamlit run streamlit_app.py
```
Browser akan otomatis terbuka ke `http://localhost:8501`.

## 4. Contoh Percakapan

```
==================================================
           SYLUS — Love and Deepspace  
==================================================
Kamu : halo Sylus
Sylus : *tersenyum tipis* Halo. Aku sudah menunggu kamu datang.
        Bagaimana harimu — ada yang ingin kamu ceritakan, atau
        kamu cuma ingin ditemani ngobrol santai malam ini?

Kamu : capek banget hari ini, kerjaan numpuk terus
Sylus : Kedengarannya berat. Kamu sudah berjuang cukup keras hari
        ini — tidak apa-apa untuk berhenti sejenak. Coba ceritakan,
        bagian mana yang paling bikin kamu lelah? Aku di sini
        mendengarkan.

Kamu : stats

Statistik Percakapan
------------------------------
Total pesan       : 4
Pesan kamu        : 2
Pesan Sylus       : 2
Total kata (kamu) : 9
Rata-rata panjang pesan kamu : 4.5 kata

Kamu : exit
Simpan riwayat percakapan sebelum keluar? (y/n): y
Riwayat disimpan ke: chat_history/sylus_chat_20260921_101500.json

Sylus : Sampai jumpa lagi. Aku akan menunggumu di sini. 🌙
```

*(Tampilan Streamlit menampilkan percakapan yang sama dalam bentuk chat bubble dengan avatar,
sidebar untuk mengatur temperature/max_tokens, serta panel statistik live — lihat screenshot
pada folder pengumpulan tugas.)*

## 5. Fitur Sesuai Spesifikasi

-  Tema roleplay NPC Sylus dengan kepribadian sesuai karakter asli & batasan konten jelas
-  System prompt terpisah dan jelas (`utils.py` → `SYSTEM_PROMPT`)
-  Conversation history dipertahankan dalam satu sesi
-  Penanganan error API tanpa crash (try/except di kedua antarmuka)
-  Perintah khusus: `exit`/`keluar`, `clear`/`reset`, plus `save`, `load`, `stats`, `help`, `panggil <nama>`
-  Panggilan personal: di awal sesi Sylus menyapa dengan "kitten" (default), tapi pengguna bisa
  langsung menentukan sebutan sendiri (di console: diminta di awal; di Streamlit: kolom "Sylus
  memanggilmu" di sidebar), dan bisa diganti kapan saja lewat perintah `panggil <nama>`
-  Streaming response di console (print bertahap) dan Streamlit (placeholder ter-update)
-  Simpan/muat riwayat percakapan ke/dari JSON
-  Statistik percakapan (jumlah pesan, kata, topik/kata yang sering muncul)
-  Kontrol parameter `temperature` & `max_tokens` (slider di Streamlit)
-  API key tidak di-hardcode — `.env` / environment variable / Colab Secrets, dengan `.env.example`
-  Kode modular: logika inti di `utils.py`, dipakai bersama oleh console app & Streamlit app

## 6. Catatan Penggunaan AI

Kerangka kode ini disusun dengan bantuan AI assistant (Claude) berdasarkan pola dari notebook
contoh perkuliahan (`kirim_pesan_streaming`, `simpan_riwayat`, dsb.), yang kemudian dikembangkan
menjadi struktur multi-file dengan persona Sylus, fitur statistik, kontrol parameter, dan
antarmuka Streamlit.