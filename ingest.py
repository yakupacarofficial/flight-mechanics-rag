"""
Ingestion: docs/*.md dosyalarini ## basliklarindan chunk'lara boler,
TF-IDF ile vektorlestirir, SQLite'a ve diske kaydeder.
Bir kez calistirilir; dokumanlar degisince tekrar calistirilir.
"""
import os
import re
import glob
import json
import sqlite3
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

DOCS_DIR = "docs"
DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"


def split_into_chunks(text, filename):
    """Bir .md dosyasini ## basliklarindan chunk'lara boler."""
    chunks = []
    # ## ile baslayan bolumlere ayir (## dahil)
    parts = re.split(r'\n(?=## )', text)
    for part in parts:
        part = part.strip()
        if not part or part.startswith('# ') and not part.startswith('## '):
            # dosya basligi (tek #) bolumunu atla
            if not part.startswith('## '):
                continue
        if not part.startswith('## '):
            continue
        # bolum basligini ayikla
        first_line = part.split('\n', 1)[0]
        section = first_line.replace('## ', '').strip()
        chunks.append({
            "source": filename,
            "section": section,
            "text": part,
        })
    return chunks


def main():
    # 1. Tum .md dosyalarini oku ve chunk'la (README haric)
    all_chunks = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        filename = os.path.basename(path)
        if filename.lower() == "readme.md":
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = split_into_chunks(text, filename)
        all_chunks.extend(chunks)
        print(f"  {filename}: {len(chunks)} chunk")

    print(f"\nToplam {len(all_chunks)} chunk bulundu.")

    if not all_chunks:
        print("Hic chunk yok. docs/ icinde ## baslikli .md dosyalari var mi?")
        return

    # 2. TF-IDF vektorlestirici egit
    texts = [c["text"] for c in all_chunks]
    vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"TF-IDF matrisi: {tfidf_matrix.shape[0]} chunk x {tfidf_matrix.shape[1]} kelime")

    # 3. SQLite'a chunk metinlerini yaz
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            source TEXT,
            section TEXT,
            text TEXT
        )
    """)
    for i, c in enumerate(all_chunks):
        conn.execute(
            "INSERT INTO chunks (id, source, section, text) VALUES (?, ?, ?, ?)",
            (i, c["source"], c["section"], c["text"]),
        )
    conn.commit()
    conn.close()
    print(f"SQLite'a yazildi: {DB_PATH}")

    # 4. Vectorizer ve matrisi diske kaydet (sorguda ayni uzay lazim)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(MATRIX_PATH, "wb") as f:
        pickle.dump(tfidf_matrix, f)
    print(f"Vektorler kaydedildi: {VECTORIZER_PATH}, {MATRIX_PATH}")

    print("\nIngestion tamamlandi.")


if __name__ == "__main__":
    main()
