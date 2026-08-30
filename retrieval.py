"""
Paylasilan retrieval katmani: TF-IDF indeksini yukler ve bir soruya
en alakali chunk'lari kosinus benzenligiyle getirir.

rag.py, app.py ve evaluate.py bu modulu kullanir; boylece indeks yukleme
mantigi, guven esigi ve baglam olusturma tek yerde tanimlidir.
"""
import sqlite3
import pickle

from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"

# En yuksek chunk skoru bunun altindaysa soruyu "bilgi tabani disi" kabul
# ederiz: modele hic gitmeden NO_ANSWER doneriz. Deger evaluate.py'deki
# etiketli test setiyle ayarlanmistir (kapsam disi sorular < 0.25).
RETRIEVAL_MIN_SCORE = 0.25

# Model prompt'una konan baglama, eslesen her chunk'in AYNI dosyadaki
# +/- bu kadar komsusu da eklenir. '##' basligindan bolme bir bolumun
# devamini koparir; komsu chunk'lar bu baglami geri kazandirir.
# Atiflar (Kaynaklar) etkilenmez; sadece eslesen chunk'lar gosterilir.
CONTEXT_WINDOW = 1

# Bağlam yetersizken verilen sabit cevap. rag.py/app.py sistem prompt'una
# da bu cumle gomulur; ikisi ayni kalsin diye burada tanimli.
NO_ANSWER = "I don't have that information in my knowledge base."


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
        {"id": rows[i][0], "score": float(scores[i]), "source": rows[i][1],
         "section": rows[i][2], "text": rows[i][3]}
        for i in top_idx
    ]


def is_confident(chunks):
    """En iyi chunk guven esigini geciyor mu?"""
    return bool(chunks) and chunks[0]["score"] >= RETRIEVAL_MIN_SCORE


def context_chunks(matched, rows, window=CONTEXT_WINDOW):
    """
    Eslesen chunk'lar + her birinin ayni dosyadaki +/- window komsusu.
    Dosya sirasinda (id'ye gore), tekrarsiz row demeti listesi doner:
    (id, source, section, text).
    """
    pos = {r[0]: idx for idx, r in enumerate(rows)}
    picked = {}
    for c in matched:
        idx = pos.get(c["id"])
        if idx is None:  # guvenlik: id eslesmezse sadece chunk'in kendisi
            picked.setdefault(
                c["id"], (c["id"], c["source"], c["section"], c["text"]))
            continue
        lo = max(0, idx - window)
        hi = min(len(rows) - 1, idx + window)
        for j in range(lo, hi + 1):
            r = rows[j]
            if r[1] == c["source"]:  # dosya sinirini asma
                picked.setdefault(r[0], r)
    return [picked[k] for k in sorted(picked)]


def build_context(matched, rows, window=CONTEXT_WINDOW):
    """Model prompt'u icin baglam metni (komsu chunk'lar dahil)."""
    return "\n\n".join(
        f"[Source: {r[1]}, Section: {r[2]}]\n{r[3]}"
        for r in context_chunks(matched, rows, window)
    )
