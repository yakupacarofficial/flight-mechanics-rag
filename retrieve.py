"""
Retrieval testi: bir soru alir, TF-IDF benzerligiyle en alakali
chunk'lari SQLite'tan getirir. Modele baglanmadan calisir.
"""
import sqlite3
import pickle
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"


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
    # soruyu ayni TF-IDF uzayina cevir
    query_vec = vectorizer.transform([query])
    # tum chunk'larla benzerligi hesapla
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    # en yuksek k tanesini sec
    top_idx = scores.argsort()[::-1][:k]
    results = []
    for i in top_idx:
        results.append({
            "score": float(scores[i]),
            "source": rows[i][1],
            "section": rows[i][2],
            "text": rows[i][3],
        })
    return results


if __name__ == "__main__":
    vectorizer, tfidf_matrix, rows = load_index()

    test_questions = [
        "What is a stall and why does it happen?",
        "Why do UAVs operate at low Reynolds numbers?",
        "How does a propeller generate thrust?",
    ]

    for q in test_questions:
        print(f"\n{'='*70}\nSORU: {q}\n{'='*70}")
        results = get_top_chunks(q, vectorizer, tfidf_matrix, rows, k=3)
        for r in results:
            print(f"\n[skor: {r['score']:.3f}] {r['source']} -> {r['section']}")
            # chunk'in ilk 150 karakterini goster
            preview = r["text"].split("\n", 1)[-1][:150].replace("\n", " ")
            print(f"    {preview}...")
