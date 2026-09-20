"""
chatbot_console.py
===================
Chatbot roleplay "Sylus" (Love and Deepspace) versi console/terminal.

Bisa dijalankan di:
- Terminal lokal   : python chatbot_console.py
- Jupyter Notebook : %run chatbot_console.py  (atau copy isi loop ke cell)
- Google Colab     : upload semua file lalu jalankan sel yang memanggil main()

Perintah khusus yang tersedia selama chat:
    exit / keluar   -> mengakhiri sesi (otomatis menawarkan simpan riwayat)
    clear / reset   -> menghapus history & memulai percakapan baru
    save            -> menyimpan riwayat percakapan saat ini ke file JSON
    load <file>     -> memuat riwayat percakapan dari file JSON
    stats           -> menampilkan statistik percakapan
    help            -> menampilkan daftar perintah
"""

import sys

from utils import (
    get_client,
    reset_history,
    set_nickname,
    stream_response,
    save_history,
    load_history,
    list_saved_histories,
    compute_stats,
    format_stats,
    MODEL_NAME,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NICKNAME,
)

BANNER = """
==================================================
           SYLUS — Love and Deepspace  
==================================================
Perintah:
  exit / keluar    -> akhiri sesi
  clear / reset    -> mulai percakapan baru
  save             -> simpan riwayat percakapan
  load <file>      -> muat riwayat dari file JSON
  panggil <nama>   -> ganti sebutan yang Sylus pakai untukmu
  stats            -> lihat statistik percakapan
  help             -> tampilkan bantuan ini lagi
==================================================
"""

HELP_TEXT = """
Perintah yang tersedia:
  exit, keluar     -> mengakhiri sesi chat
  clear, reset     -> menghapus riwayat & memulai obrolan baru
  save             -> menyimpan riwayat percakapan ke file JSON
  load <namafile>  -> memuat riwayat percakapan dari file JSON
  panggil <nama>   -> mengganti sebutan yang Sylus pakai untukmu
  stats            -> menampilkan statistik percakapan saat ini
  help             -> menampilkan pesan bantuan ini
"""


def print_saved_files_hint():
    files = list_saved_histories()
    if files:
        print(f"(File riwayat tersimpan, contoh: {files[0]})")


def main():
    print(BANNER)

    try:
        client = get_client()
    except ValueError as e:
        print(f"⚠️ {e}")
        sys.exit(1)

    nickname = input(
        "Sylus : Hai kitten, atau kau ingin menggunakan panggilan lain? (kosongkan untuk 'kitten'): "
    ).strip() or DEFAULT_NICKNAME

    messages = reset_history(nickname)
    temperature = DEFAULT_TEMPERATURE
    max_tokens = DEFAULT_MAX_TOKENS
    current_filename = None

    print(f"\nSylus : Baiklah, {nickname}. Senang bisa mengobrol denganmu. Ada apa hari ini?\n")

    while True:
        try:
            user_input = input("Kamu : ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\nSylus : Sampai jumpa lagi {nickname}. Jaga dirimu baik-baik.")
            break

        if not user_input:
            print("Silakan ketik sesuatu, atau 'help' untuk melihat perintah.\n")
            continue

        cmd = user_input.lower()

        # --- Perintah khusus ---
        if cmd in ("exit", "keluar"):
            if len(messages) > 1:
                jawab = input("Simpan riwayat percakapan sebelum keluar? (y/n): ").strip().lower()
                if jawab == "y":
                    path = save_history(messages, current_filename)
                    print(f"Riwayat disimpan ke: {path}")
            print(f"\nSylus : Kau sudah bosan mengobrol denganku {nickname}? Hahaha. Bailah, Sampai jumpa lagi.")
            break

        if cmd in ("clear", "reset"):
            messages = reset_history(nickname)
            current_filename = None
            print("\n(Percakapan telah direset. Sylus siap memulai obrolan baru.)\n")
            continue

        if cmd.startswith("panggil"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print(f"Gunakan: panggil <nama>. Saat ini Sylus memanggilmu '{nickname}'.\n")
            else:
                nickname = parts[1].strip()
                messages = set_nickname(messages, nickname)
                print(f"\nSylus : Baiklah, mulai sekarang aku akan memanggilmu '{nickname}'.\n")
            continue

        if cmd == "save":
            path = save_history(messages, current_filename)
            print(f"Riwayat percakapan disimpan ke: {path}\n")
            continue

        if cmd.startswith("load"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("Gunakan: load <nama_file.json>")
                print_saved_files_hint()
            else:
                try:
                    messages = load_history(parts[1])
                    print(f"Riwayat percakapan berhasil dimuat dari: {parts[1]}\n")
                except Exception as e:
                    print(f"⚠️ Gagal memuat file: {e}\n")
            continue

        if cmd == "stats":
            print()
            print(format_stats(compute_stats(messages)))
            print()
            continue

        if cmd == "help":
            print(HELP_TEXT)
            continue

        # --- Pesan biasa ke LLM ---
        messages.append({"role": "user", "content": user_input})

        try:
            full_answer = ""
            print("Sylus : ", end="", flush=True)
            for delta in stream_response(client, messages, MODEL_NAME, temperature, max_tokens):
                print(delta, end="", flush=True)
                full_answer += delta
            print("\n")
            messages.append({"role": "assistant", "content": full_answer})

        except Exception as e:
            # Program tidak boleh crash walau API gagal — buang pesan user tadi
            # supaya history tidak rusak, lalu lanjutkan loop percakapan.
            print(f"Maaf {nickname}, aku tidak bisa berbincang denganmu sekarang (error API: {e}). "
                    "Hubungi aku lagi nanti."
                )
            messages.pop()


if __name__ == "__main__":
    main()