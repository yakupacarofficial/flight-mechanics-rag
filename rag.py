"""
Tam RAG: soru -> retrieval (TF-IDF) -> baglam -> Phi-3.5 Mini -> cevap.
Model sadece getirilen chunk'lara dayanarak cevap verir. En iyi chunk
guven esiginin altindaysa model hic cagrilmaz, dogrudan NO_ANSWER doner.
"""
from foundry import chat, get_endpoint
from retrieval import (
    NO_ANSWER, build_context, get_top_chunks, is_confident, load_index,
)


def answer_query(question, base_url, model, vectorizer, tfidf_matrix, rows):
    # 1. Retrieval: en alakali chunk'lari bul
    chunks = get_top_chunks(question, vectorizer, tfidf_matrix, rows, k=3)

    # 2. Guven kontrolu: yeterince alakali chunk yoksa modele hic gitme
    if not is_confident(chunks):
        return NO_ANSWER, chunks

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

    # 5. Modele gonder
    answer = chat(base_url, model, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ])
    return answer, chunks


if __name__ == "__main__":
    url, model = get_endpoint()
    print(f"[servis: {url} | model: {model}]\n")
    vectorizer, tfidf_matrix, rows = load_index()

    print("Flight Mechanics RAG. Soru sor (cikmak icin bos birak + Enter).\n")
    while True:
        question = input("Soru: ").strip()
        if not question:
            break
        answer, chunks = answer_query(
            question, url, model, vectorizer, tfidf_matrix, rows
        )
        print(f"\nCevap:\n{answer}\n")
        print("Kaynaklar:", ", ".join(f"{c['source']}({c['section']})" for c in chunks))
        print("-" * 70)
