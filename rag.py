"""
Tam RAG: soru -> retrieval (TF-IDF) -> baglam -> Phi-3.5 Mini -> cevap.
Model sadece getirilen chunk'lara dayanarak cevap verir.
"""
import sqlite3
import pickle
import openai
import requests
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"


def get_endpoint():
    """Calisan Foundry servisini ve chat modelini otomatik bulur."""
    for port in (50034, 5273, 49947):
        try:
            url = f"http://127.0.0.1:{port}/v1"
            models = requests.get(f"{url}/models", timeout=2).json()
            for m in models["data"]:
                if "phi-3.5" in m["id"].lower():
                    return url, m["id"]
            return url, models["data"][0]["id"]
        except Exception:
            continue
    raise RuntimeError("Foundry servisi bulunamadi. 'foundry service status' calisiyor mu?")


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


def answer_query(question, client, model, vectorizer, tfidf_matrix, rows):
    # 1. Retrieval: en alakali chunk'lari bul
    chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)

    # 2. Baglami olustur (kaynak bilgisiyle)
    context = "\n\n".join(
        f"[Source: {c['source']}, Section: {c['section']}]\n{c['text']}"
        for c in chunks
    )

    # 3. Sistem talimati: sadece baglami kullan, bilmiyorsan soyle
    system_prompt = (
        "You are a flight-mechanics teaching assistant. Answer the user's "
        "question using ONLY the provided context below. If the context does "
        "not contain the answer, say 'I don't have that information in my "
        "knowledge base.' Cite the source file when relevant. Be concise.\n\n"
        f"CONTEXT:\n{context}"
    )

    # 4. Modele gonder
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content, chunks


if __name__ == "__main__":
    url, model = get_endpoint()
    print(f"[servis: {url} | model: {model}]\n")
    client = openai.OpenAI(base_url=url, api_key="not-needed")
    vectorizer, tfidf_matrix, rows = load_index()

    print("Flight Mechanics RAG. Soru sor (cikmak icin bos birak + Enter).\n")
    while True:
        question = input("Soru: ").strip()
        if not question:
            break
        answer, chunks = answer_query(
            question, client, model, vectorizer, tfidf_matrix, rows
        )
        print(f"\nCevap:\n{answer}\n")
        print("Kaynaklar:", ", ".join(f"{c['source']}({c['section']})" for c in chunks))
        print("-" * 70)
