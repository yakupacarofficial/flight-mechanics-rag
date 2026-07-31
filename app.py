"""
Streamlit web arayuzu: Flight Mechanics RAG asistani.
Calistirmak icin: streamlit run app.py
"""
import sqlite3
import pickle
import openai
import requests
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"


def get_endpoint():
    # Foundry portu her baslatmada degisir; once bilinen portlari, sonra
    # servis durumundan okunan portu dene.
    ports = []
    try:
        import subprocess
        out = subprocess.run(["foundry", "service", "status"],
                             capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"127\.0\.0\.1:(\d+)", out)
        if m:
            ports.append(int(m.group(1)))
    except Exception:
        pass
    ports += [55913, 55333, 54901, 50034, 5273, 49947]
    for port in ports:
        try:
            url = f"http://127.0.0.1:{port}/v1"
            models = requests.get(f"{url}/models", timeout=2).json()
            for mm in models["data"]:
                if "phi-3.5" in mm["id"].lower():
                    return url, mm["id"]
            return url, models["data"][0]["id"]
        except Exception:
            continue
    return None, None


# @st.cache_resource: agir yuklemeyi bir kez yapar, her etkilesimde tekrarlamaz
@st.cache_resource
def load_index():
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    with open(MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, source, section, text FROM chunks").fetchall()
    conn.close()
    return vectorizer, tfidf_matrix, rows


def get_top_chunks(query, vectorizer, tfidf_matrix, rows, k=3):
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    top_idx = scores.argsort()[::-1][:k]
    return [
        {"score": float(scores[i]), "source": rows[i][1],
         "section": rows[i][2], "text": rows[i][3]}
        for i in top_idx
    ]


def answer_query(question, base_url, model, chunks):
    context = "\n\n".join(
        f"[Source: {c['source']}, Section: {c['section']}]\n{c['text']}"
        for c in chunks
    )
    system_prompt = (
        "You are a flight-mechanics teaching assistant. Answer the user's "
        "question using ONLY the provided context below. If the context does "
        "not contain the answer, say 'I don't have that information in my "
        "knowledge base.' Cite the source file when relevant. Be concise.\n\n"
        f"CONTEXT:\n{context}"
    )
    # openai kutuphanesi yerine dogrudan requests: istegi tek parca gonderir,
    # boylece Foundry'nin "request body timed out" hatasi olusmaz.
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    sess = requests.Session()
    sess.trust_env = False  # proxy ortam degiskenlerini yoksay (yerel istek)
    resp = sess.post(f"{base_url}/chat/completions", json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"Foundry {resp.status_code}: {resp.text[:500]}")
    return resp.json()["choices"][0]["message"]["content"]


# ---------- ARAYUZ ----------

st.set_page_config(page_title="Flight Mechanics RAG", page_icon="✈️")

st.title("✈️ Flight Mechanics RAG")
st.caption("Yerel, offline calisir. Cevaplar sadece bilgi tabanindaki notlara dayanir.")

# Servisi ve indeksi hazirla
url, model = get_endpoint()
if url is None:
    st.error("Foundry servisi bulunamadi. Terminalde 'foundry service start' calistirin.")
    st.stop()

vectorizer, tfidf_matrix, rows = load_index()
client = openai.OpenAI(base_url=url, api_key="not-needed", timeout=120.0)

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
    with st.spinner("Retrieval + model calisiyor..."):
        chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)
        answer = answer_query(question, url, model, chunks)

    st.subheader("Cevap")
    st.write(answer)

    st.subheader("Kaynaklar")
    for c in chunks:
        st.markdown(f"**{c['source']}** — {c['section']}  (skor: {c['score']:.3f})")
