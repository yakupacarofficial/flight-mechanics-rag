"""
Streamlit web arayuzu: Flight Mechanics RAG asistani (cok turlu sohbet).
Calistirmak icin: streamlit run app.py
"""
import streamlit as st

from foundry import chat_stream, get_endpoint
from rag import MAX_HISTORY_MESSAGES
from retrieval import NO_ANSWER, build_context, get_top_chunks, is_confident
from retrieval import load_index as _load_index

# @st.cache_resource: agir yuklemeyi bir kez yapar, her etkilesimde tekrarlamaz
load_index = st.cache_resource(_load_index)


def answer_stream(question, base_url, model, chunks, rows, history=None):
    """Cevabi parca parca uretir (st.write_stream ile canli yazilir)."""
    context = build_context(chunks, rows)
    system_prompt = (
        "You are a flight-mechanics teaching assistant. Answer the user's "
        "question using ONLY the provided context below. If the context does "
        f"not contain the answer, say '{NO_ANSWER}' Cite the source file when "
        "relevant. Be concise.\n\n"
        f"CONTEXT:\n{context}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages += (history or [])[-MAX_HISTORY_MESSAGES:]
    messages.append({"role": "user", "content": question})
    return chat_stream(base_url, model, messages)


def render_sources(chunks):
    with st.expander("Kaynaklar — cevabin buradan gelip gelmedigini kontrol et"):
        for c in chunks:
            st.markdown(f"**{c['source']}** — {c['section']}  (skor: {c['score']:.3f})")
            # chunk metni '## Baslik' satiriyla basliyor; basligi atla
            body = c["text"].split("\n", 1)[1] if "\n" in c["text"] else c["text"]
            st.caption(body.strip())


# ---------- ARAYUZ ----------

st.set_page_config(page_title="Flight Mechanics RAG", page_icon="✈️")

st.title("✈️ Flight Mechanics RAG")
st.caption("Yerel, offline calisir. Cevaplar sadece bilgi tabanindaki notlara dayanir.")

# Servisi ve indeksi hazirla
try:
    url, model = get_endpoint()
except RuntimeError as e:
    st.error(str(e))
    st.stop()

vectorizer, tfidf_matrix, rows = load_index()

col_info, col_clear = st.columns([4, 1])
col_info.success(f"Bagli: {model}  •  {len(rows)} chunk yuklu")
if col_clear.button("Sohbeti temizle"):
    st.session_state.history = []

with st.expander("Ornek sorular"):
    st.markdown(
        "- What is a stall and why does it happen?\n"
        "- Why do UAVs operate at low Reynolds numbers?\n"
        "- Explain the difference between Static and Dynamic Stability.\n"
        "- What is the best airfoil for a supersonic jet? (kapsam disi)"
    )

st.session_state.setdefault("history", [])

# Onceki turlari goster (kaynaklariyla)
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            render_sources(msg["sources"])

question = st.chat_input("Sorunuzu yazin")
if question:
    with st.chat_message("user"):
        st.write(question)

    # Modele gidecek gecmis: mevcut turdan onceki mesajlar (rol + icerik)
    prior = [{"role": m["role"], "content": m["content"]}
             for m in st.session_state.history]

    chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)
    grounded = is_confident(chunks)

    with st.chat_message("assistant"):
        if not grounded:
            answer = NO_ANSWER  # yeterince alakali chunk yok: modele hic gitme
            st.write(answer)
        else:
            answer = st.write_stream(
                answer_stream(question, url, model, chunks, rows, prior)
            )
            render_sources(chunks)

    st.session_state.history += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer,
         "sources": chunks if answer != NO_ANSWER else None},
    ]
