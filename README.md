# Flight Mechanics RAG

A fully local, offline Retrieval-Augmented Generation (RAG) assistant that answers flight-mechanics and aerodynamics questions using a personal knowledge base, powered by Microsoft Foundry Local and Phi-3.5 Mini. No cloud, no API keys, no data leaves the machine.

Tamamen yerel ve cevrimdisi calisan, ucus mekanigi ve aerodinamik sorularini kisisel bir bilgi tabanina dayanarak yanitlayan bir RAG asistani. Microsoft Foundry Local ve Phi-3.5 Mini ile.

Built for the Microsoft Summer 2026 program.

---

## English

### What is this?

Large language models are knowledgeable but have two weaknesses: they don't know your private documents, and they sometimes make things up (hallucinate). This project solves both with the RAG (Retrieval-Augmented Generation) pattern:

1. **Retrieve** - find the most relevant passages from a local knowledge base for a given question
2. **Augment** - inject those passages into the model's prompt as context
3. **Generate** - the model answers using only that context, and says "I don't know" when the answer isn't there

Everything runs on-device via Microsoft Foundry Local, making it suitable for offline, air-gapped, or privacy-sensitive environments.

### Architecture
- **Knowledge base:** 8 Markdown files, ~39 chunks, covering fluid mechanics, airfoils, finite wings, drag, control & stability, flight performance, propellers/drones, and atmosphere.
- **Retrieval:** two-stage. A TF-IDF cosine pass ([scikit-learn](https://scikit-learn.org/)) picks a candidate pool, then the pool is re-ranked by a blend of TF-IDF and a hand-rolled BM25 (`HYBRID_ALPHA`). Chosen because Foundry Local's catalog has no embedding model; both signals are word-overlap based, fully offline, no extra model download. The confidence gate always uses the raw TF-IDF score.
- **Storage:** SQLite for chunk text/metadata; pickled TF-IDF vectorizer and matrix.
- **Generation:** Phi-3.5 Mini via Foundry Local's OpenAI-compatible local API.

### Tech stack

| Component | Choice | Why |
|-----------|--------|-----|
| Model runtime | Microsoft Foundry Local | On-device inference, OpenAI-compatible API |
| Language model | Phi-3.5 Mini | Small, fast, good quality; runs on Apple Silicon GPU |
| Retrieval | scikit-learn TF-IDF + BM25 re-rank | No embedding model needed; ideal for small corpora |
| Storage | SQLite | Serverless, single-file, built into Python |
| Web UI | Streamlit | Pure-Python web interface |

### Project structure

```
ingest.py         Build the index: split docs/*.md on ## headings, fit TF-IDF,
                  write knowledge.db + vectorizer.pkl + tfidf_matrix.pkl
retrieval.py      Shared retrieval: index loading, TF-IDF + BM25 re-rank,
                  confidence gate (RETRIEVAL_MIN_SCORE), neighbour-context builder
foundry.py        Foundry Local connection: port discovery, service auto-start,
                  chat() / chat_stream() helpers (raw requests, no body-timeout)
rag.py            Command-line RAG loop + answer_query() (used by evaluate.py)
app.py            Streamlit multi-turn web UI with per-answer source panels
retrieve.py       Retrieval-only diagnostic (prints top chunks, no model)
evaluate.py       Labelled evaluation: retrieval metrics, and --generate for
                  end-to-end grounding / refusal checks
docs/             Knowledge base: 8 Markdown files (~39 chunks)
tests/            pytest suite (pure logic, no Foundry service needed)
.github/workflows CI: runs pytest on every push and PR
```

### Setup

Prerequisites: macOS with Apple Silicon (M1+), Homebrew, Python 3.12.

```bash
# 1. Install Foundry Local and download the model
brew tap microsoft/foundrylocal
brew install foundrylocal
foundry model run phi-3.5-mini      # downloads ~2 GB once, then /exit

# 2. Set up the Python environment
python3.12 -m venv venvrag
source venvrag/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
# Build the knowledge base (run once, or after editing docs/)
python ingest.py

# Option A - command-line interface
python rag.py

# Option B - web interface
streamlit run app.py         # opens http://localhost:8501
```

The model service is started automatically if it isn't already running; you can also start it yourself with `foundry service start`.

Both interfaces are multi-turn and stream the answer token by token as the model generates it. The last few messages are carried into the prompt so follow-ups like "why does it happen?" resolve against the previous answer; retrieval still runs on the current question only. The web interface additionally shows an expandable panel for each retrieved chunk, so you can read the exact passage an answer was drawn from.

Set `RAG_LOG=turns.jsonl` before `python rag.py` to append one JSON line per turn (question, retrieved chunk scores, latency, whether it was answered) for later analysis.

Note on ports: Foundry Local assigns a random port on each restart. Port discovery is automatic ([foundry.py](foundry.py)): it reads the current port from `foundry service status`, falling back to a list of known ports. If the service isn't running at all, it is started (`foundry service start`) and waited for. To force a specific endpoint, set `FOUNDRY_ENDPOINT=http://127.0.0.1:PORT` (or `FOUNDRY_PORT=PORT`); to disable auto-start, set `FOUNDRY_NO_AUTOSTART=1`.

### Evaluation

Retrieval quality was measured with a labeled test set of 14 questions across three difficulty levels (direct recall, contextual synthesis, engineering scenarios) plus two deliberately out-of-scope questions.

```bash
python evaluate.py
```

| Metric | Result |
|--------|--------|
| Answerable questions | 12 |
| Hit@3 (correct source in top-3) | 12/12 = 100% |
| Top-1 (correct source ranked first) | 12/12 = 100% |
| Out-of-scope questions correctly rejected (score < 0.25) | 2/2 |

Score distribution is meaningful: term-specific questions score high (Bernoulli 0.62, IAS/TAS 0.58), while broader questions score lower (Reynolds 0.36) but still retrieve the correct source. The two out-of-scope questions (aircraft classification and supersonic airfoils, topics intentionally left out of the knowledge base) fell below the confidence threshold, so the assistant correctly declined to answer.

**End-to-end generation** (`python evaluate.py --generate`, requires the Foundry service) additionally calls the model for every question and checks the answer, not just retrieval:

| Metric | Result |
|--------|--------|
| Lexical grounding ≥ 0.50 (answer vocabulary traceable to retrieved context) | 11/12 |
| Average grounding | 0.66 |
| False refusals (answerable question → "I don't know") | 0/12 |
| Out-of-scope → model answered "I don't have that information" | 2/2 |

Grounding is an approximate offline proxy (fraction of the answer's content words, minus question words, that appear in the retrieved context); paraphrasing and synonyms lower it, so ~0.65 reflects a faithful-but-reworded answer rather than verbatim copying. The context handed to the model is the matched chunks plus their immediate neighbours in the same file ([retrieval.py](retrieval.py), `CONTEXT_WINDOW`), which restores continuity broken by splitting on `##` headings; citations still list only the chunks that actually matched. The confidence gate (`RETRIEVAL_MIN_SCORE`) short-circuits both out-of-scope questions before the model is even called; the same constant is the threshold used in this report.

### Tests

Unit tests cover the pure logic — chunk splitting, the confidence gate, neighbour-context expansion (including file-boundary and dedup cases), Foundry port-list resolution, and the grounding/refusal helpers. They need no Foundry service and run in about a second.

```bash
pip install -r requirements-dev.txt
pytest
```

CI runs the same suite on every push and pull request ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

### Design decisions & limitations

- **Why TF-IDF + BM25 instead of semantic embeddings?** Foundry Local's catalog contains no embedding model. Rather than adding an external dependency, retrieval uses word-overlap signals only: TF-IDF cosine for the candidate pool, then a BM25 re-rank (term-frequency saturation + document-length normalisation) to steady the ordering of near-tied supporting chunks. Both are fast and fully offline. On this small, well-separated knowledge base retrieval was already at 100% Hit@3 with pure TF-IDF, so BM25 is insurance for questions outside the test set rather than a headline gain; set `HYBRID_ALPHA = 1.0` in [retrieval.py](retrieval.py) for pure TF-IDF.
- **Why local?** Privacy, offline capability, and suitability for air-gapped or defense environments where cloud LLMs cannot be used.
- **Model size trade-off:** Phi-3.5 Mini prioritizes speed over depth; occasionally it appends a redundant disclaimer. Larger models would improve nuance at the cost of latency.

---

## Turkce

### Bu proje nedir?

Buyuk dil modelleri bilgilidir ama iki zayifligi vardir: senin ozel dokumanlarini bilmezler ve bazen bilgi uydururlar (halusinasyon). Bu proje ikisini de RAG (Retrieval-Augmented Generation, Getirmeyle Zenginlestirilmis Uretim) deseniyle cozer:

1. **Getirme:** Soruyla ilgili en alakali bolumleri yerel bilgi tabanindan bul
2. **Zenginlestirme:** Bu bolumleri modele baglam olarak ver
3. **Uretim:** Model sadece bu baglama dayanarak cevap versin; cevap yoksa "bilmiyorum" desin

Her sey Microsoft Foundry Local ile cihaz uzerinde calisir; cevrimdisi, kapali ag veya gizlilik gerektiren ortamlar icin uygundur.

### Mimari
- **Bilgi tabani:** 8 Markdown dosyasi, ~39 parca; akiskanlar mekanigi, kanat profilleri, sonlu kanat, surukleme, kontrol ve kararlilik, ucus performansi, pervaneler/dronlar ve atmosfer konularini kapsar.
- **Retrieval:** iki asamali. TF-IDF kosinus ([scikit-learn](https://scikit-learn.org/)) bir aday havuzu secer, sonra havuz TF-IDF ile elle yazilmis bir BM25'in karisimiyla (`HYBRID_ALPHA`) yeniden siralanir. Foundry Local kataloğunda embedding modeli bulunmadigi icin tercih edildi; iki sinyal de sozcuk-ortusmesine dayanir, tamamen cevrimdisi, ek model indirmesi yok. Guven kapisi her zaman ham TF-IDF skorunu kullanir.
- **Depolama:** Parca metni ve bilgileri icin SQLite; TF-IDF vektorlestirici ve matris icin pickle dosyalari.
- **Uretim:** Foundry Local'in OpenAI-uyumlu yerel API'si uzerinden Phi-3.5 Mini.

### Teknoloji secimleri

| Bilesen | Secim | Neden |
|---------|-------|-------|
| Model calisma ortami | Microsoft Foundry Local | Cihaz uzeri cikarim, OpenAI-uyumlu API |
| Dil modeli | Phi-3.5 Mini | Kucuk, hizli, kaliteli; Apple Silicon GPU'da calisir |
| Retrieval | scikit-learn TF-IDF + BM25 yeniden siralama | Embedding modeli gerektirmez; kucuk veri icin ideal |
| Depolama | SQLite | Sunucusuz, tek dosya, Python'da yerlesik |
| Web arayuzu | Streamlit | Saf Python web arayuzu |

### Proje yapisi

```
ingest.py         Indeksi kur: docs/*.md'yi ## basliklarindan bol, TF-IDF egit,
                  knowledge.db + vectorizer.pkl + tfidf_matrix.pkl yaz
retrieval.py      Paylasilan retrieval: indeks yukleme, TF-IDF + BM25 yeniden
                  siralama, guven kapisi (RETRIEVAL_MIN_SCORE), komsu-baglam
foundry.py        Foundry Local baglantisi: port kesfi, servis auto-start,
                  chat() / chat_stream() yardimcilari (ham requests, timeout yok)
rag.py            Komut satiri RAG dongusu + answer_query() (evaluate.py kullanir)
app.py            Streamlit cok turlu web arayuzu, cevap basina kaynak panelleri
retrieve.py       Yalniz retrieval tanisi (en iyi chunk'lari yazar, model yok)
evaluate.py       Etiketli degerlendirme: retrieval metrikleri; --generate ile
                  uctan uca grounding / reddetme kontrolleri
docs/             Bilgi tabani: 8 Markdown dosyasi (~39 chunk)
tests/            pytest takimi (saf mantik, Foundry servisi gerekmez)
.github/workflows CI: her push ve PR'da pytest calistirir
```

### Kurulum

Gereksinimler: Apple Silicon (M1+) islemcili macOS, Homebrew, Python 3.12.

```bash
# 1. Foundry Local'i kur ve modeli indir
brew tap microsoft/foundrylocal
brew install foundrylocal
foundry model run phi-3.5-mini      # ~2 GB bir kez iner, sonra /exit

# 2. Python ortamini kur
python3.12 -m venv venvrag
source venvrag/bin/activate
pip install -r requirements.txt
```

### Kullanim

```bash
# Bilgi tabanini olustur (bir kez, ya da docs/ degisince)
python ingest.py

# Secenek A - komut satiri arayuzu
python rag.py

# Secenek B - web arayuzu
streamlit run app.py         # http://localhost:8501 acilir
```

Model servisi calismiyorsa otomatik baslatilir; dilerseniz kendiniz de `foundry service start` ile baslatabilirsiniz.

Her iki arayuz de cok turludur ve cevabi model urettikce token token akitir. Son birkac mesaj prompt'a tasinir, boylece "peki neden olur?" gibi takip sorulari onceki cevaba gore cozulur; retrieval yine yalnizca guncel soruya gore calisir. Web arayuzu ayrica getirilen her chunk icin acilir bir panel gosterir; boylece cevabin dayandigi tam pasaji okuyabilirsiniz.

Port notu: Foundry Local her yeniden baslatmada rastgele bir port atar. Port bulma otomatiktir ([foundry.py](foundry.py)): guncel port `foundry service status` ciktisindan okunur, bulunamazsa bilinen portlar denenir. Servis hic calismiyorsa baslatilir (`foundry service start`) ve ayaga kalkmasi beklenir. Belirli bir adresi zorlamak icin `FOUNDRY_ENDPOINT=http://127.0.0.1:PORT` (veya `FOUNDRY_PORT=PORT`); otomatik baslatmayi kapatmak icin `FOUNDRY_NO_AUTOSTART=1` ayarlayin.

### Degerlendirme

Retrieval kalitesi, uc zorluk seviyesinde (dogrudan bilgi getirme, baglamsal sentez, muhendislik senaryolari) 14 soruluk etiketli bir test setiyle olculdu; ikisi bilerek kapsam disi birakildi.

```bash
python evaluate.py
```

| Metrik | Sonuc |
|--------|-------|
| Cevaplanabilir soru | 12 |
| Hit@3 (dogru kaynak ilk 3'te) | 12/12 = %100 |
| Top-1 (dogru kaynak 1. sirada) | 12/12 = %100 |
| Dogru reddedilen kapsam disi soru (skor < 0.25) | 2/2 |

Skor dagilimi anlamlidir: terime ozgu sorular yuksek (Bernoulli 0.62, IAS/TAS 0.58), daha genel sorular dusuk (Reynolds 0.36) skor alir ama yine de dogru kaynagi getirir. Iki kapsam disi soru (ucak siniflandirmasi ve supersonik kanat profilleri, bilgi tabanina bilerek alinmayan konular) guven esiginin altinda kaldigi icin asistan dogru sekilde cevap vermeyi reddetti.

**Uctan uca uretim** (`python evaluate.py --generate`, Foundry servisi calisir olmali) ek olarak her soru icin modeli cagirir ve sadece retrieval'i degil cevabin kendisini de kontrol eder:

| Metrik | Sonuc |
|--------|-------|
| Sozcuksel grounding ≥ 0.50 (cevap kelimeleri getirilen baglamda geciyor mu) | 11/12 |
| Ortalama grounding | 0.66 |
| Yanlis reddetme (cevaplanabilir soru → "bilmiyorum") | 0/12 |
| Kapsam disi → model "bilgi tabanimda yok" dedi | 2/2 |

Grounding yaklasik, cevrimdisi bir olcuttur (cevabin icerik kelimelerinin, soru kelimeleri haric, getirilen baglamda gecen orani); paraphrase ve es anlamli sozcukler bu orani dusurur, dolayisiyla ~0.65 birebir kopyalama degil "sadik ama yeniden ifade edilmis" bir cevabi gosterir. Modele verilen baglam, eslesen chunk'lar + ayni dosyadaki bitisik komsularidir ([retrieval.py](retrieval.py), `CONTEXT_WINDOW`); bu, `##` basligindan bolmenin kopardigi sureklilikligi geri kazandirir. Atiflar yalnizca gercekten eslesen chunk'lari listeler. Guven kapisi (`RETRIEVAL_MIN_SCORE`) iki kapsam disi soruyu model cagrilmadan once kesip atar; bu rapordaki esik de ayni sabittir.

### Testler

Birim testleri saf mantigi kapsar: chunk bolme, guven kapisi, komsu-baglam genisletme (dosya siniri ve tekrar durumlari dahil), Foundry port listesi cozumu ve grounding/reddetme yardimcilari. Foundry servisi gerektirmez, yaklasik bir saniyede calisir.

```bash
pip install -r requirements-dev.txt
pytest
```

CI ayni takimi her push ve pull request'te calistirir ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

### Tasarim kararlari ve sinirlamalar

- **Neden semantik embedding yerine TF-IDF + BM25?** Foundry Local kataloğunda embedding modeli yok. Disaridan bagimlilik eklemek yerine retrieval yalnizca sozcuk-ortusme sinyalleri kullanir: aday havuzu icin TF-IDF kosinus, ardindan berabere yakin destek chunk'larinin siralamasini oturtmak icin BM25 yeniden siralama (terim-frekansi doygunlugu + belge-uzunlugu normalizasyonu). Ikisi de hizli ve tamamen cevrimdisi. Bu kucuk, konulari net ayrik bilgi tabaninda saf TF-IDF zaten %100 Hit@3 veriyordu; BM25 headline bir kazanim degil, test-seti disi sorular icin sigortadir. Saf TF-IDF icin [retrieval.py](retrieval.py)'de `HYBRID_ALPHA = 1.0` yapin.
- **Neden yerel?** Gizlilik, cevrimdisi calisabilme ve bulut LLM'lerin kullanilamadigi kapali ag/savunma ortamlarina uygunluk.
- **Model boyutu odunlesimi:** Phi-3.5 Mini hizi derinlige tercih eder; ara sira gereksiz bir uyari cumlesi ekleyebilir. Daha buyuk modeller nuansi artirir ama gecikme pahasina.

---

## License / Lisans

Knowledge base notes are original English summaries written while studying an aviation-theory textbook; no text is copied verbatim from the source.

Bilgi tabani notlari, bir ucus teorisi kitabi calisilirken yazilmis ozgun Ingilizce ozetlerdir; kaynaktan hicbir metin birebir kopyalanmamistir.
