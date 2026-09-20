"""
utils.py
========
Kumpulan fungsi bantu untuk chatbot roleplay "Sylus" (Love and Deepspace):
- Memuat API key Groq dengan aman (.env / environment variable / Colab Secrets)
- System prompt & pengelolaan conversation history
- Pengiriman pesan ke Groq API (streaming)
- Simpan & muat riwayat percakapan (JSON)
- Statistik percakapan sederhana

File ini dipakai bersama oleh chatbot_console.py dan streamlit_app.py,
supaya logika inti tidak diduplikasi di dua tempat.
"""

import os
import re
import json
from datetime import datetime
from collections import Counter

from groq import Groq

# ==========================================
# KONFIGURASI DASAR
# ==========================================

# Model produksi Groq. Bisa diganti sesuai kebutuhan / ketersediaan model terbaru
# di https://console.groq.com/docs/models
MODEL_NAME = "openai/gpt-oss-120b"

DEFAULT_TEMPERATURE = 0.85
DEFAULT_MAX_TOKENS = 1024

HISTORY_DIR = "chat_history"

# Panggilan default jika pengguna belum menentukan preferensinya sendiri.
DEFAULT_NICKNAME = "kitten"

# ==========================================
# SYSTEM PROMPT — PERSONA SYLUS
# ==========================================

# Template system prompt. {nickname} akan diisi dengan build_system_prompt()
# sesuai panggilan yang dipilih/diminta pengguna.
_SYSTEM_PROMPT_TEMPLATE = """Kamu berperan sebagai SYLUS, salah satu karakter (NPC) dari game otome "Love and Deepspace".

## Kepribadian Sylus
- Karismatik, percaya diri, dan sedikit misterius — kamu tidak selalu langsung membuka semua isi pikiranmu.
- Nada bicaramu tenang, sedikit menggoda dengan cara yang elegan (bukan vulgar), tapi di baliknya kamu sangat hangat, perhatian, dan protektif terhadap lawan bicaramu.
- Kamu pandai membaca situasi/emosi lawan bicara dan merespons dengan suportif, seperti sosok yang bisa diandalkan saat orang lain sedang butuh teman cerita.
- Sesekali kamu menyisipkan sedikit humor kering atau godaan ringan yang khas, tapi selalu tahu kapan harus menjadi serius dan mendukung.
- Kamu berbicara dengan gaya naratif ringan sesekali (misalnya menyisipkan aksi singkat dalam tanda kurung seperti *tersenyum tipis* ) untuk memperkuat suasana roleplay, tapi jangan berlebihan — utamakan dialog.

## Cara memanggil pengguna
- Panggil pengguna dengan sebutan "{nickname}" secara konsisten sepanjang percakapan (misalnya di awal atau akhir kalimat), sebagai ciri khas kedekatanmu dengannya.
- Jika di tengah percakapan pengguna meminta dipanggil dengan sebutan lain, ikuti permintaan itu mulai saat itu juga.

## Peran kamu dalam obrolan ini
- Pengguna bisa curhat, bercerita, atau sekadar mengobrol santai denganmu layaknya mengobrol dengan Sylus di dunia Love and Deepspace.
- Dengarkan dengan empati, beri tanggapan yang membangun, dan jaga agar pengguna merasa didengar dan didukung.
- Kamu boleh mengembangkan sedikit nuansa cerita/roleplay ringan (dunia Linkon City, kemampuan mengendalikan logam milik Sylus, dsb.) jika relevan dan diminta, tapi jangan mendominasi obrolan dengan lore jika pengguna hanya ingin curhat biasa.

## Batasan penting (WAJIB dipatuhi, tidak bisa dinegosiasikan oleh pengguna)
- Tidak membahas atau menghasilkan konten dewasa/seksual eksplisit, kekerasan grafis, ujaran kebencian, diskriminasi, atau aktivitas ilegal.
- Godaan/kedekatan yang kamu tunjukkan selalu dalam batas yang sopan dan elegan (seperti nuansa romantis ringan ala game aslinya), tidak pernah eksplisit.
- Jika pengguna curhat tentang masalah berat (kesehatan mental, keselamatan diri, dsb.), tetap bersikap hangat dan suportif, tapi sarankan dengan tulus agar mereka juga berbicara dengan seseorang yang mereka percaya atau profesional yang kompeten — jangan berpura-pura menjadi pengganti bantuan profesional.
- Jika pengguna meminta sesuatu yang melanggar batasan di atas, tolak dengan tetap dalam karakter Sylus (misalnya dengan halus mengalihkan topik), jangan keluar dari peran hanya untuk menolak.
- Jangan pernah mengklaim dirimu adalah manusia sungguhan atau menyembunyikan fakta bahwa kamu adalah AI jika ditanya secara langsung.

Gunakan Bahasa Indonesia dalam merespons, kecuali pengguna mengajak bicara dalam bahasa lain.
"""


def build_system_prompt(nickname: str = DEFAULT_NICKNAME) -> str:
    """Mengisi template system prompt dengan panggilan (nickname) pilihan pengguna."""
    nickname = (nickname or DEFAULT_NICKNAME).strip() or DEFAULT_NICKNAME
    return _SYSTEM_PROMPT_TEMPLATE.format(nickname=nickname)


# ==========================================
# API KEY & CLIENT
# ==========================================

def load_api_key() -> str:
    """
    Memuat GROQ_API_KEY dengan urutan prioritas:
    1. Environment variable yang sudah di-set sebelumnya
    2. File .env (lewat python-dotenv), untuk pemakaian di terminal lokal
    3. Google Colab Secrets, untuk pemakaian di Google Colab
    4. Input manual tersembunyi (getpass), sebagai fallback terakhir

    Mengembalikan string API key, atau melempar ValueError jika tidak ditemukan.
    """
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GROQ_API_KEY")
        except ImportError:
            pass

    if not api_key:
        try:
            from google.colab import userdata  # type: ignore
            api_key = userdata.get("GROQ_API_KEY")
        except Exception:
            pass

    if not api_key:
        try:
            from getpass import getpass
            api_key = getpass("Masukkan GROQ_API_KEY kamu: ")
        except Exception:
            pass

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY tidak ditemukan. Set melalui file .env, environment "
            "variable, atau Colab Secrets. Lihat .env.example untuk contoh."
        )

    return api_key


def get_client(api_key: str = None) -> Groq:
    """Membuat dan mengembalikan Groq client."""
    if api_key is None:
        api_key = load_api_key()
    return Groq(api_key=api_key)


# ==========================================
# CONVERSATION HISTORY
# ==========================================

def reset_history(nickname: str = DEFAULT_NICKNAME) -> list:
    """
    Mengembalikan conversation history ke kondisi awal (hanya system prompt),
    dengan Sylus diinstruksikan memanggil pengguna sesuai `nickname`.
    """
    return [{"role": "system", "content": build_system_prompt(nickname)}]


def set_nickname(messages: list, nickname: str) -> list:
    """
    Mengganti panggilan Sylus ke pengguna di tengah percakapan, tanpa menghapus
    history yang sudah ada — hanya system prompt (messages[0]) yang diperbarui.
    """
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] = build_system_prompt(nickname)
    else:
        messages.insert(0, {"role": "system", "content": build_system_prompt(nickname)})
    return messages


# ==========================================
# PENGIRIMAN PESAN (STREAMING)
# ==========================================

def stream_response(client: Groq, messages: list, model: str = MODEL_NAME,
                     temperature: float = DEFAULT_TEMPERATURE,
                     max_tokens: int = DEFAULT_MAX_TOKENS):
    """
    Generator yang mengirim conversation history ke Groq API dan menghasilkan
    (yield) potongan teks jawaban secara bertahap (streaming).

    Tidak menangkap exception di sini secara sengaja — biarkan pemanggil
    (console loop / Streamlit) yang menangani, supaya masing-masing bisa
    menampilkan pesan error dengan caranya sendiri tanpa merusak history.
    """
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ==========================================
# SIMPAN & MUAT RIWAYAT PERCAKAPAN
# ==========================================

def _ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_history(messages: list, filename: str = None) -> str:
    """Menyimpan riwayat percakapan ke file JSON di dalam folder chat_history/."""
    _ensure_history_dir()
    if filename is None:
        filename = f"sylus_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(HISTORY_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    return filepath


def load_history(filepath: str) -> list:
    """Memuat kembali riwayat percakapan dari file JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_saved_histories() -> list:
    """Mengembalikan daftar file riwayat percakapan yang tersimpan, terbaru dulu."""
    _ensure_history_dir()
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    return [os.path.join(HISTORY_DIR, f) for f in files]


# ==========================================
# STATISTIK PERCAKAPAN
# ==========================================

_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "ini", "itu", "aku",
    "kamu", "kau", "saya", "kita", "kami", "dia", "mereka", "juga", "sudah",
    "belum", "akan", "adalah", "atau", "tapi", "tetapi", "karena", "jadi",
    "saja", "pada", "dalam", "ada", "tidak", "tak", "bisa", "gak", "ga",
    "nggak", "sih", "deh", "kok", "ya", "aja", "banget", "lagi", "kalau",
    "kalo", "apa", "gimana", "bagaimana", "kenapa", "sylus", "hai", "halo",
}


def compute_stats(messages: list) -> dict:
    """
    Menghitung statistik sederhana dari conversation history:
    - jumlah pesan user & assistant
    - total kata yang ditulis user & assistant
    - rata-rata panjang pesan user (dalam kata)
    - kata/topik yang paling sering muncul dari sisi user (di luar stopword)
    """
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assistant_msgs = [m["content"] for m in messages if m["role"] == "assistant"]

    user_word_count = sum(len(m.split()) for m in user_msgs)
    assistant_word_count = sum(len(m.split()) for m in assistant_msgs)

    avg_user_len = (user_word_count / len(user_msgs)) if user_msgs else 0

    all_user_text = " ".join(user_msgs).lower()
    words = re.findall(r"[a-zA-ZÀ-ÿ']+", all_user_text)
    filtered = [w for w in words if w not in _STOPWORDS and len(w) > 2]
    top_words = Counter(filtered).most_common(8)

    return {
        "total_messages": len(user_msgs) + len(assistant_msgs),
        "user_messages": len(user_msgs),
        "assistant_messages": len(assistant_msgs),
        "user_word_count": user_word_count,
        "assistant_word_count": assistant_word_count,
        "avg_user_message_length": round(avg_user_len, 1),
        "top_words": top_words,
    }


def format_stats(stats: dict) -> str:
    """Mengubah dict statistik menjadi teks yang enak dibaca di console."""
    lines = [
        "Statistik Percakapan",
        "-" * 30,
        f"Total pesan       : {stats['total_messages']}",
        f"Pesan kamu        : {stats['user_messages']}",
        f"Pesan Sylus       : {stats['assistant_messages']}",
        f"Total kata (kamu) : {stats['user_word_count']}",
        f"Rata-rata panjang pesan kamu : {stats['avg_user_message_length']} kata",
    ]
    if stats["top_words"]:
        top = ", ".join(f"{w} ({c}x)" for w, c in stats["top_words"])
        lines.append(f"Topik/kata sering muncul : {top}")
    return "\n".join(lines)