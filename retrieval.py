"""
Paylasilan retrieval katmani: TF-IDF indeksini yukler ve bir soruya
en alakali chunk'lari getirir.

Siralama iki asamalidir: once TF-IDF kosinus benzerligiyle bir aday
havuzu alinir, sonra bu havuz TF-IDF ve BM25 skorlarinin agirlikli
ortalamasiyla (HYBRID_ALPHA) yeniden siralanir. TF-IDF sozcuk-vektoru
ortusmesine, BM25 terim-frekansi doygunlugu + belge-uzunlugu
normalizasyonuna bakar; ikisi birlikte tek-terimli sorularda daha
kararli siralama verir. Guven esigi HAM TF-IDF skoruyla degerlendirilir
(hibrit siralamadan etkilenmez).

rag.py, app.py ve evaluate.py bu modulu kullanir; boylece indeks yukleme
mantigi, guven esigi ve baglam olusturma tek yerde tanimlidir.
"""
import math
import sqlite3
import pickle
from collections import Counter

from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"

# En yuksek HAM TF-IDF skoru bunun altindaysa soruyu "bilgi tabani disi"
# kabul ederiz: modele hic gitmeden NO_ANSWER doneriz. Deger evaluate.py'
# deki etiketli test setiyle ayarlanmistir (kapsam disi sorular < 0.25).
RETRIEVAL_MIN_SCORE = 0.25

# Hibrit siralama: nihai skor = ALPHA*norm(tfidf) + (1-ALPHA)*norm(bm25),
# aday havuzu icinde min-max normalize edilerek. 1.0 = saf TF-IDF (BM25
# hesabi atlanir), 0.0 = saf BM25.
HYBRID_ALPHA = 0.5
# TF-IDF ile alinip hibritle yeniden siralanan aday sayisi.
CANDIDATE_POOL = 10
# BM25 Okapi parametreleri (standart varsayilanlar).
_BM25_K1 = 1.5
_BM25_B = 0.75

# Model prompt'una konan baglama, eslesen her chunk'in AYNI dosyadaki
# +/- bu kadar komsusu da eklenir. '##' basligindan bolme bir bolumun
# devamini koparir; komsu chunk'lar bu baglami geri kazandirir.
# Atiflar (Kaynaklar) etkilenmez; sadece eslesen chunk'lar gosterilir.
CONTEXT_WINDOW = 1

# Bağlam yetersizken verilen sabit cevap. rag.py/app.py sistem prompt'una
# da bu cumle gomulur; ikisi ayni kalsin diye burada tanimli.
NO_ANSWER = "I don't have that information in my knowledge base."

# Selamlama / tesekkur / "ne yapabilirsin" gibi mesajlar bilgi sorusu
# degildir; bunlara NO_ANSWER yerine kisa bir sohbet yaniti doneriz.
GREETING_REPLY = (
    "Merhaba! Ucus mekanigi ve aerodinamik sorularini, elimdeki ders "
    "notlarina dayanarak yanitliyorum. Ornek: \"What is a stall and why "
    "does it happen?\""
)
THANKS_REPLY = "Rica ederim! Baska bir sorun olursa buradayim."

_GREETINGS = {
    "selam", "selamlar", "merhaba", "mrb", "meraba", "hey", "hi", "hello",
    "hi there", "hey there", "gunaydin", "gunaydın", "iyi gunler", "iyi günler",
    "iyi aksamlar", "iyi akşamlar", "iyi geceler", "naber", "naber",
    "nasilsin", "nasılsın", "selam nasilsin", "selam nasılsın",
    "merhaba nasilsin", "merhaba nasılsın", "yo",
}
_THANKS = {
    "tesekkurler", "teşekkürler", "tesekkur ederim", "teşekkür ederim",
    "sag ol", "sağ ol", "sagol", "sağol", "eyvallah", "thanks", "thank you",
    "thx", "ty",
}
_META = {
    "kimsin", "sen kimsin", "ne yapabilirsin", "ne yaparsin", "ne yaparsın",
    "ne ise yararsin", "ne işe yararsın", "yardim", "yardım", "help",
    "who are you", "what can you do", "napiyorsun", "napıyorsun",
}


def smalltalk_reply(question):
    """
    Soru bir selamlama/tesekkur/meta mesajiysa kisa bir sohbet yaniti,
    degilse None doner. Yanlis pozitif olmasin diye TAM eslesme aranir
    (noktalama ve fazla bosluk temizlenerek).
    """
    q = " ".join(question.strip().lower().rstrip("!?. ").split())
    if q in _GREETINGS or q in _META:
        return GREETING_REPLY
    if q in _THANKS:
        return THANKS_REPLY
    return None


def load_index():
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    with open(MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, source, section, text FROM chunks").fetchall()
    conn.close()
    return vectorizer, tfidf_matrix, rows


def bm25_scores(query, rows, vectorizer):
    """
    Her chunk icin BM25 Okapi skoru: {row_index: score}. Tokenizasyon
    TF-IDF ile ayni olsun diye vectorizer'in analyzer'i kullanilir.
    Kucuk bilgi tabani icin sorgu basina yeniden hesap onemsizdir.
    """
    analyze = vectorizer.build_analyzer()
    docs = [analyze(r[3]) for r in rows]
    n_docs = len(docs)
    doc_len = [len(d) for d in docs]
    avgdl = (sum(doc_len) / n_docs) if n_docs else 0.0
    tf = [Counter(d) for d in docs]

    df = Counter()
    for counts in tf:
        df.update(counts.keys())

    q_terms = analyze(query)
    idf = {
        t: math.log((n_docs - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5) + 1)
        for t in set(q_terms)
    }

    scores = {}
    for i, counts in enumerate(tf):
        s = 0.0
        for t in q_terms:
            f = counts.get(t, 0)
            if not f:
                continue
            norm = 1 - _BM25_B + _BM25_B * (doc_len[i] / avgdl if avgdl else 0.0)
            s += idf[t] * (f * (_BM25_K1 + 1)) / (f + _BM25_K1 * norm)
        scores[i] = s
    return scores


def _minmax(values):
    """{i: v} -> {i: [0,1]}. Tum degerler esitse hepsi 0."""
    lo, hi = min(values.values()), max(values.values())
    span = hi - lo
    return {i: ((v - lo) / span if span else 0.0) for i, v in values.items()}


def get_top_chunks(query, vectorizer, tfidf_matrix, rows, k=3):
    query_vec = vectorizer.transform([query])
    tfidf = cosine_similarity(query_vec, tfidf_matrix)[0]

    pool = list(tfidf.argsort()[::-1][:max(k, CANDIDATE_POOL)])

    if HYBRID_ALPHA >= 1.0:
        ranked = pool                                    # saf TF-IDF
    else:
        bm = bm25_scores(query, rows, vectorizer)
        tn = _minmax({i: float(tfidf[i]) for i in pool})
        bn = _minmax({i: float(bm[i]) for i in pool})
        ranked = sorted(
            pool,
            key=lambda i: HYBRID_ALPHA * tn[i] + (1 - HYBRID_ALPHA) * bn[i],
            reverse=True,
        )

    return [
        {"id": rows[i][0], "score": float(tfidf[i]), "source": rows[i][1],
         "section": rows[i][2], "text": rows[i][3]}
        for i in ranked[:k]
    ]


def is_confident(chunks):
    """
    Getirilen chunk'lardan HERHANGI biri ham TF-IDF guven esigini geciyor
    mu? (Hibrit yeniden siralama en iyi TF-IDF chunk'ini 1. siradan
    kaydirabilir, o yuzden ilk chunk degil maksimum bakilir.)
    """
    return bool(chunks) and max(c["score"] for c in chunks) >= RETRIEVAL_MIN_SCORE


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
