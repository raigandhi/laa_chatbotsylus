"""
streamlit_app.py
=================
Antarmuka web (Streamlit) untuk chatbot roleplay "Sylus" (Love and Deepspace).

Jalankan dengan:
    streamlit run streamlit_app.py
"""

import streamlit as st

from utils import (
    get_client,
    reset_history,
    set_nickname,
    stream_response,
    save_history,
    load_history,
    compute_stats,
    MODEL_NAME,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NICKNAME,
)

st.set_page_config(
    page_title="Sylus — Love and Deepspace",
    page_icon="asset/ava_mephisto",
    layout="centered",
)

# ==========================================
# STATE AWAL
# ==========================================

if "nickname" not in st.session_state:
    st.session_state.nickname = DEFAULT_NICKNAME

if "messages" not in st.session_state:
    st.session_state.messages = reset_history(st.session_state.nickname)

if "client" not in st.session_state:
    try:
        st.session_state.client = get_client()
        st.session_state.api_error = None
    except ValueError as e:
        st.session_state.client = None
        st.session_state.api_error = str(e)

# ==========================================
# SIDEBAR — KONTROL & FITUR TAMBAHAN
# ==========================================

with st.sidebar:
    st.markdown("### Sylus Chat")
    st.caption("Mulai berbincang dengan sylus disini")

    st.markdown("---")
    st.markdown("#### Hai kitten")
    new_nickname = st.text_input(
        "Apa kau ingin menggunakan panggilan lain? (kosongkan untuk 'kitten'): ", value=st.session_state.nickname,
        help="Ganti sebutan yang dipakai Sylus untuk kamu, misalnya nama atau panggilan sayang.",
    )
    if new_nickname.strip() and new_nickname.strip() != st.session_state.nickname:
        st.session_state.nickname = new_nickname.strip()
        st.session_state.messages = set_nickname(st.session_state.messages, st.session_state.nickname)
        st.toast(f"Sylus sekarang memanggilmu '{st.session_state.nickname}'.")

    st.markdown("---")
    st.markdown("#### Parameter LLM")
    temperature = st.slider(
        "Temperature (kreativitas)", min_value=0.0, max_value=1.5,
        value=DEFAULT_TEMPERATURE, step=0.05,
        help="Rendah = konsisten & fokus, Tinggi = lebih variatif/ekspresif.",
    )
    max_tokens = st.slider(
        "Max tokens (panjang jawaban)", min_value=128, max_value=2048,
        value=DEFAULT_MAX_TOKENS, step=64,
    )

    st.markdown("---")
    st.markdown("#### Aksi")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset", use_container_width=True):
            st.session_state.messages = reset_history(st.session_state.nickname)
            st.rerun()
    with col2:
        if st.button("Simpan", use_container_width=True):
            if len(st.session_state.messages) > 1:
                path = save_history(st.session_state.messages)
                st.success(f"Tersimpan: {path}")
            else:
                st.warning("Belum ada percakapan untuk disimpan.")

    uploaded = st.file_uploader("Muat riwayat (.json)", type=["json"])
    if uploaded is not None:
        try:
            import json
            st.session_state.messages = json.load(uploaded)
            st.success("Riwayat berhasil dimuat.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal memuat file: {e}")

    st.markdown("---")
    st.markdown("#### Statistik Percakapan")
    stats = compute_stats(st.session_state.messages)
    st.metric("Total pesan", stats["total_messages"])
    mcol1, mcol2 = st.columns(2)
    mcol1.metric("Pesan kamu", stats["user_messages"])
    mcol2.metric("Pesan Sylus", stats["assistant_messages"])
    if stats["top_words"]:
        st.caption("Topik sering muncul:")
        st.write(", ".join(f"`{w}` ({c}x)" for w, c in stats["top_words"]))

# ==========================================
# HALAMAN UTAMA — CHAT
# ==========================================

st.title("Sylus")
st.caption("Karismatik, sedikit misterius, tapi selalu ada untukmu.")

if st.session_state.api_error:
    st.error(
        f"⚠️ {st.session_state.api_error}\n\n"
        "Set `GROQ_API_KEY` melalui file `.env`, environment variable, atau Colab Secrets."
    )
    st.stop()

# Tampilkan riwayat percakapan (skip system prompt)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    avatar = "asset/ava_sylus.png" if msg["role"] == "assistant" else "asset/ava_mc.png"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Input pengguna
user_input = st.chat_input("Ketik pesan untuk Sylus...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="asset/ava_mc.png"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="asset/ava_sylus.png"):
        placeholder = st.empty()
        full_answer = ""
        try:
            for delta in stream_response(
                st.session_state.client,
                st.session_state.messages,
                MODEL_NAME,
                temperature,
                max_tokens,
            ):
                full_answer += delta
                placeholder.markdown(full_answer + "▌")
            placeholder.markdown(full_answer)
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

        except Exception as e:
            # Program tidak boleh crash walau API gagal.
            st.session_state.messages.pop()  # buang pesan user agar history tidak rusak
            placeholder.error(f"Maaf, aku tidak bisa berbincang denganmu sekarang (error API: {e}). "
                    "Hubungi aku lagi nanti."
                )