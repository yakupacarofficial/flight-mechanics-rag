# Flight Mechanics RAG

[![CI](https://github.com/yakupacarofficial/flight-mechanics-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/yakupacarofficial/flight-mechanics-rag/actions/workflows/ci.yml)

A **fully local, offline** assistant that answers flight-mechanics and aerodynamics
questions from a personal set of notes. Powered by Microsoft Foundry Local + Phi-3.5 Mini.
No cloud, no API keys, no data leaves the machine.

*Built for the Microsoft Summer 2026 program.*

---

## English

### The idea

LLMs have two weak spots: they don't know your private notes, and they sometimes
make things up. **RAG (Retrieval-Augmented Generation)** fixes both:

1. **Retrieve** the most relevant passages from a local knowledge base
2. **Augment** the model's prompt with those passages
3. **Generate** an answer *only* from that context — or say "I don't know"

### Pipeline

```
question
   │
   ▼
retrieve  ──►  TF-IDF cosine  →  BM25 re-rank          (top 3 chunks + scores)
   │
   ▼
confidence gate ─── score < 0.25 ? ──► "I don't have that in my knowledge base"
   │ (passes)
   ▼
build context  ──►  matched chunks + their neighbours in the same file
   │
   ▼
Phi-3.5 Mini (Foundry Local)  ──►  answer streamed token by token  +  sources
```

### Quickstart

```bash
# 1. Model runtime (once)
brew tap microsoft/foundrylocal && brew install foundrylocal
foundry model run phi-3.5-mini          # ~2 GB download, then /exit

# 2. Python env
python3.12 -m venv venvrag && source venvrag/bin/activate
pip install -r requirements.txt

# 3. Build the index (once, or after editing docs/)
python ingest.py

# 4. Ask questions
python rag.py                # command line
streamlit run app.py         # web UI at http://localhost:8501
```

The Foundry service auto-starts and its port is auto-detected — nothing to configure.

### Results

```bash
python evaluate.py               # retrieval only (fast)
python evaluate.py --generate    # also calls the model and checks the answer
```

Labelled test set: 12 answerable questions (3 difficulty levels) + 2 deliberately out-of-scope.

| Metric | Result |
|--------|--------|
| Hit@3 — correct source file in top 3 | **12 / 12** |
| Top-1 — correct source file ranked first | **12 / 12** |
| Out-of-scope questions correctly refused | **2 / 2** |
| Answer grounded in retrieved context (≥ 0.50) | **11 / 12**, avg 0.66 |
| Wrong refusals on answerable questions | **0 / 12** |

### How it works — key decisions

| Decision | Why |
|----------|-----|
| **Local only** | Privacy; works air-gapped / offline; suitable where cloud LLMs aren't allowed |
| **TF-IDF + BM25, no embeddings** | Foundry Local ships no embedding model; both are word-overlap, fully offline, zero extra download |
| **Confidence gate** | If the best match scores below a threshold, answer "I don't know" *without calling the model* |
| **Greetings & small talk** | "Hi", "thanks", "what can you do?" get a short conversational reply — the "not in my knowledge base" line is reserved for genuine out-of-scope questions |
| **Neighbour context** | Splitting notes on `##` headings cuts continuity — the model also gets the chunk before/after each match |
| **Multi-turn + streaming** | Follow-ups ("why does it happen?") use recent history; answers stream token by token |
| **Tested** | 72 pytest unit tests on the pure logic; CI runs them on every push |

**Limitations:** Phi-3.5 Mini favours speed over depth and sometimes appends a redundant
disclaimer. On this small, well-separated knowledge base pure TF-IDF already hit 100% Hit@3,
so BM25 is insurance for questions outside the test set rather than a headline gain.

### Project layout

```
ingest.py      build the index (split docs on ## → TF-IDF → SQLite + pickles)
retrieval.py   retrieval + BM25 re-rank + confidence gate + context builder
foundry.py     Foundry Local: port discovery, service auto-start, chat helpers
rag.py         command-line RAG loop
app.py         Streamlit multi-turn web UI
evaluate.py    labelled evaluation (retrieval, and --generate end-to-end)
docs/          the knowledge base — 8 Markdown files (~39 chunks)
tests/         pytest suite (no Foundry service needed)
```

---

## Türkçe

### Fikir

Büyük dil modellerinin iki zayıf noktası var: senin özel notlarını bilmezler ve bazen
bilgi uydururlar. **RAG (Getirmeyle Zenginleştirilmiş Üretim)** ikisini de çözer:

1. **Getir** — soruyla ilgili en alakalı bölümleri yerel bilgi tabanından bul
2. **Zenginleştir** — bu bölümleri modele bağlam olarak ver
3. **Üret** — model *yalnızca* bu bağlamdan cevap versin; yoksa "bilmiyorum" desin

### İşleyiş

```
soru
  │
  ▼
getir  ──►  TF-IDF kosinüs  →  BM25 yeniden sıralama       (en iyi 3 chunk + skor)
  │
  ▼
güven kapısı ─── skor < 0.25 ? ──► "bilgi tabanımda bu bilgi yok"
  │ (geçer)
  ▼
bağlam kur  ──►  eşleşen chunk'lar + aynı dosyadaki komşuları
  │
  ▼
Phi-3.5 Mini (Foundry Local)  ──►  cevap token token akar  +  kaynaklar
```

### Hızlı başlangıç

```bash
# 1. Model çalışma ortamı (bir kez)
brew tap microsoft/foundrylocal && brew install foundrylocal
foundry model run phi-3.5-mini          # ~2 GB iner, sonra /exit

# 2. Python ortamı
python3.12 -m venv venvrag && source venvrag/bin/activate
pip install -r requirements.txt

# 3. İndeksi kur (bir kez, ya da docs/ değişince)
python ingest.py

# 4. Soru sor
python rag.py                # komut satırı
streamlit run app.py         # web arayüzü — http://localhost:8501
```

Foundry servisi otomatik başlar ve portu otomatik bulunur — ayar gerekmez.

### Sonuçlar

```bash
python evaluate.py               # sadece retrieval (hızlı)
python evaluate.py --generate    # modeli de çağırıp cevabı kontrol eder
```

Etiketli test seti: 12 cevaplanabilir soru (3 zorluk seviyesi) + 2 bilerek kapsam dışı.

| Metrik | Sonuç |
|--------|-------|
| Hit@3 — doğru kaynak dosya ilk 3'te | **12 / 12** |
| Top-1 — doğru kaynak dosya 1. sırada | **12 / 12** |
| Kapsam dışı sorular doğru reddedildi | **2 / 2** |
| Cevap getirilen bağlama dayanıyor (≥ 0.50) | **11 / 12**, ort. 0.66 |
| Cevaplanabilir soruda yanlış reddetme | **0 / 12** |

### Nasıl çalışır — temel kararlar

| Karar | Neden |
|-------|-------|
| **Yalnızca yerel** | Gizlilik; kapalı ağ / çevrimdışı çalışır; bulut LLM'lerin yasak olduğu yerlere uygun |
| **TF-IDF + BM25, embedding yok** | Foundry Local'de embedding modeli yok; ikisi de sözcük-örtüşmesi, tamamen çevrimdışı, ek indirme yok |
| **Güven kapısı** | En iyi eşleşme eşiğin altındaysa modeli *hiç çağırmadan* "bilmiyorum" der |
| **Selamlaşma & sohbet** | "Selam", "teşekkürler", "ne yapabilirsin?" kısa bir sohbet yanıtı alır — "bilgi tabanımda yok" cevabı yalnızca gerçek kapsam-dışı sorulara kalır |
| **Komşu bağlam** | Notları `##` başlıklarından bölmek sürekliliği koparır — model her eşleşmenin bir önceki/sonraki chunk'ını da alır |
| **Çok turlu + streaming** | Takip soruları ("peki neden olur?") son mesajları kullanır; cevap token token akar |
| **Testli** | Saf mantık için 72 pytest testi; CI her push'ta çalıştırır |

**Sınırlar:** Phi-3.5 Mini hızı derinliğe tercih eder, ara sıra gereksiz bir uyarı cümlesi
ekler. Bu küçük, konuları net ayrık bilgi tabanında saf TF-IDF zaten %100 Hit@3 verdi;
BM25 headline bir kazanım değil, test-seti dışı sorular için sigortadır.

### Proje düzeni

```
ingest.py      indeksi kur (docs'u ## ile böl → TF-IDF → SQLite + pickle)
retrieval.py   retrieval + BM25 yeniden sıralama + güven kapısı + bağlam
foundry.py     Foundry Local: port keşfi, servis auto-start, chat yardımcıları
rag.py         komut satırı RAG döngüsü
app.py         Streamlit çok turlu web arayüzü
evaluate.py    etiketli değerlendirme (retrieval ve --generate uçtan uca)
docs/          bilgi tabanı — 8 Markdown dosyası (~39 chunk)
tests/         pytest takımı (Foundry servisi gerekmez)
```

---

## License / Lisans

Knowledge base notes are original English summaries written while studying an
aviation-theory textbook; no text is copied verbatim from the source.

Bilgi tabanı notları, bir uçuş teorisi kitabı çalışılırken yazılmış özgün İngilizce
özetlerdir; kaynaktan hiçbir metin birebir kopyalanmamıştır.
