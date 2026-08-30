"""
Tam RAG: soru -> retrieval (TF-IDF) -> baglam -> Phi-3.5 Mini -> cevap.
Model sadece getirilen chunk'lara dayanarak cevap verir. En iyi chunk
guven esiginin altindaysa model hic cagrilmaz, dogrudan NO_ANSWER doner.
Onceki turlar baglama katilir (takip sorulari icin); retrieval yine
yalnizca son soruya gore yapilir.
"""
import json
import os
import time

from foundry import chat, chat_stream, get_endpoint
from retrieval import (
    NO_ANSWER, build_context, get_top_chunks, is_confident, load_index,
)

# Modele tasinan sohbet gecmisinin ust siniri (mesaj sayisi = tur * 2).
MAX_HISTORY_MESSAGES = 6

# RAG_LOG=path.jsonl ayarliysa her tur (soru, chunk skorlari, sure) bu
# dosyaya bir JSON satiri olarak eklenir. Sonradan analiz icin.
LOG_PATH = os.environ.get("RAG_LOG")


def _log_turn(question, chunks, answer, total_ms):
    if not LOG_PATH:
        return
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": question,
        "answered": answer != NO_ANSWER,
        "total_ms": round(total_ms, 1),
        "chunks": [{"source": c["source"], "section": c["section"],
                    "score": round(c["score"], 4)} for c in chunks],
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def answer_query(question, base_url, model, vectorizer, tfidf_matrix, rows,
                 history=None, stream=False):
    """
    (cevap, chunks) doner. stream=True ise 'cevap' bir metin-parcasi
    uretecidir (guven kapisi tetiklenirse tek parcalik).
    """
    # 1. Retrieval: en alakali chunk'lari bul (yalnizca son soruya gore)
    chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)

    # 2. Guven kontrolu: yeterince alakali chunk yoksa modele hic gitme
    if not is_confident(chunks):
        return (iter([NO_ANSWER]) if stream else NO_ANSWER), chunks

    # 3. Baglami olustur (eslesen chunk'lar + ayni dosyadaki komsulari)
    context = build_context(chunks, rows)

    # 4. Sistem talimati: sadece baglami kullan, bilmiyorsan soyle
    system_prompt = (
        "You are a flight-mechanics teaching assistant. Answer the user's "
        "question using ONLY the provided context below. If the context does "
        f"not contain the answer, say '{NO_ANSWER}' Cite the source file when "
        "relevant. Be concise.\n\n"
        f"CONTEXT:\n{context}"
    )

    # 5. Modele gonder: sistem + (kirpilmis) gecmis + guncel soru
    messages = [{"role": "system", "content": system_prompt}]
    messages += (history or [])[-MAX_HISTORY_MESSAGES:]
    messages.append({"role": "user", "content": question})
    send = chat_stream if stream else chat
    return send(base_url, model, messages), chunks


if __name__ == "__main__":
    url, model = get_endpoint()
    print(f"[servis: {url} | model: {model}]\n")
    vectorizer, tfidf_matrix, rows = load_index()

    print("Flight Mechanics RAG. Soru sor (cikmak icin bos birak + Enter).\n")
    history = []
    while True:
        question = input("Soru: ").strip()
        if not question:
            break
        t0 = time.perf_counter()
        stream, chunks = answer_query(
            question, url, model, vectorizer, tfidf_matrix, rows, history,
            stream=True,
        )
        print("\nCevap:")
        parts = []
        for delta in stream:
            print(delta, end="", flush=True)
            parts.append(delta)
        answer = "".join(parts)
        print("\n")
        print("Kaynaklar:", ", ".join(f"{c['source']}({c['section']})" for c in chunks))
        print("-" * 70)
        _log_turn(question, chunks, answer, (time.perf_counter() - t0) * 1000)
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": answer}]
        history = history[-MAX_HISTORY_MESSAGES:]
