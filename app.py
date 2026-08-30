"""
Streamlit web arayuzu: Flight Mechanics RAG asistani.
Calistirmak icin: streamlit run app.py
"""
import streamlit as st

from foundry import chat, get_endpoint
from retrieval import NO_ANSWER, build_context, get_top_chunks, is_confident
from retrieval import load_index as _load_index

# @st.cache_resource: agir yuklemeyi bir kez yapar, her etkilesimde tekrarlamaz
load_index = st.cache_resource(_load_index)


def answer_query(question, base_url, model, chunks, rows):
    # Baglam: eslesen chunk'lar + ayni dosyadaki komsulari
    context = build_context(chunks, rows)
    system_prompt = (
        "You are a flight-mechanics teaching assistant. Answer the user's "
        "question using ONLY the provided context below. If the context does "
        f"not contain the answer, say '{NO_ANSWER}' Cite the source file when "
        "relevant. Be concise.\n\n"
        f"CONTEXT:\n{context}"
    )
    return chat(base_url, model, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ])


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

st.success(f"Bagli: {model}  •  {len(rows)} chunk yuklu")

# Ornek sorular (tiklaninca kutuya yazilir)
with st.expander("Ornek sorular"):
    st.markdown(
        "- What is a stall and why does it happen?\n"
        "- Why do UAVs operate at low Reynolds numbers?\n"
        "- Explain the difference between Static and Dynamic Stability.\n"
        "- What is the best airfoil for a supersonic jet? (kapsam disi)"
    )

question = st.text_input("Sorunuzu yazin:", placeholder="What is a stall and why does it happen?")

if question:
    chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)
    if not is_confident(chunks):
        # Yeterince alakali chunk yok: modele hic gitme
        answer = NO_ANSWER
    else:
        with st.spinner("Retrieval + model calisiyor..."):
            answer = answer_query(question, url, model, chunks, rows)

    st.subheader("Cevap")
    st.write(answer)

    st.subheader("Kaynaklar")
    st.caption("Eslesen bolumler. Ac ve cevabin buradan gelip gelmedigini kontrol et.")
    for c in chunks:
        with st.expander(f"{c['source']} — {c['section']}  (skor: {c['score']:.3f})"):
            # chunk metni '## Baslik' satiriyla basliyor; baslik zaten
            # expander etiketinde var, tekrar gostermeyelim.
            body = c["text"].split("\n", 1)[1] if "\n" in c["text"] else c["text"]
            st.markdown(body.strip())
