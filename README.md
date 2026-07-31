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
- **Retrieval:** TF-IDF vectorization + cosine similarity (scikit-learn). Chosen because Foundry Local's catalog has no embedding model; TF-IDF is the same approach used in Microsoft's reference RAG blog and works well for small knowledge bases, fully offline, no extra model download.
- **Storage:** SQLite for chunk text/metadata; pickled TF-IDF vectorizer and matrix.
- **Generation:** Phi-3.5 Mini via Foundry Local's OpenAI-compatible local API.

### Tech stack

| Component | Choice | Why |
|-----------|--------|-----|
| Model runtime | Microsoft Foundry Local | On-device inference, OpenAI-compatible API |
| Language model | Phi-3.5 Mini | Small, fast, good quality; runs on Apple Silicon GPU |
| Retrieval | scikit-learn TF-IDF | No embedding model needed; ideal for small corpora |
| Storage | SQLite | Serverless, single-file, built into Python |
| Web UI | Streamlit | Pure-Python web interface |

### Project structure
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
# Start the local model service (leave running)
foundry service start

# Build the knowledge base (run once, or after editing docs/)
python ingest.py

# Option A - command-line interface
python rag.py

# Option B - web interface
streamlit run app.py         # opens http://localhost:8501
```

Note on ports: Foundry Local assigns a random port on each restart. If the app can't connect, run `foundry service status` to get the current port and add it to the port list in app.py / rag.py.

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

### Design decisions & limitations

- **Why TF-IDF instead of semantic embeddings?** Foundry Local's catalog contains no embedding model. Rather than adding an external dependency, we used TF-IDF (word-overlap similarity), the same method as Microsoft's reference RAG example. It's fast and fully offline, but sees words rather than meaning, so for multi-topic questions like "stall," the single best chunk can rank second. For this small, well-separated knowledge base the impact is negligible (100% Hit@3).
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
- **Retrieval:** TF-IDF vektorlestirme + kosinus benzerligi (scikit-learn). Foundry Local kataloğunda embedding modeli bulunmadigi icin tercih edildi; TF-IDF, Microsoft'un referans RAG blog yazisinin da kullandigi yontemdir ve kucuk bilgi tabanlarinda iyi calisir, tamamen cevrimdisi.
- **Depolama:** Parca metni ve bilgileri icin SQLite; TF-IDF vektorlestirici ve matris icin pickle dosyalari.
- **Uretim:** Foundry Local'in OpenAI-uyumlu yerel API'si uzerinden Phi-3.5 Mini.

### Teknoloji secimleri

| Bilesen | Secim | Neden |
|---------|-------|-------|
| Model calisma ortami | Microsoft Foundry Local | Cihaz uzeri cikarim, OpenAI-uyumlu API |
| Dil modeli | Phi-3.5 Mini | Kucuk, hizli, kaliteli; Apple Silicon GPU'da calisir |
| Retrieval | scikit-learn TF-IDF | Embedding modeli gerektirmez; kucuk veri icin ideal |
| Depolama | SQLite | Sunucusuz, tek dosya, Python'da yerlesik |
| Web arayuzu | Streamlit | Saf Python web arayuzu |

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
# Yerel model servisini baslat (acik birak)
foundry service start

# Bilgi tabanini olustur (bir kez, ya da docs/ degisince)
python ingest.py

# Secenek A - komut satiri arayuzu
python rag.py

# Secenek B - web arayuzu
streamlit run app.py         # http://localhost:8501 acilir
```

Port notu: Foundry Local her yeniden baslatmada rastgele bir port atar. Uygulama baglanamazsa, `foundry service status` ile guncel portu ogrenip app.py / rag.py icindeki port listesine ekleyin.

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

### Tasarim kararlari ve sinirlamalar

- **Neden semantik embedding yerine TF-IDF?** Foundry Local kataloğunda embedding modeli yok. Disaridan bagimlilik eklemek yerine, Microsoft'un referans RAG orneğiyle ayni yontem olan TF-IDF (sozcuk-ortusme benzerligi) kullanildi. Hizli ve tamamen cevrimdisidir, ama anlami degil kelimeleri gorur, bu yuzden "stall" gibi cok-konulu sorularda en isabetli parca ikinci siraya dusebilir. Bu kucuk ve konulari net ayrik bilgi tabaninda etki ihmal edilebilir (%100 Hit@3).
- **Neden yerel?** Gizlilik, cevrimdisi calisabilme ve bulut LLM'lerin kullanilamadigi kapali ag/savunma ortamlarina uygunluk.
- **Model boyutu odunlesimi:** Phi-3.5 Mini hizi derinlige tercih eder; ara sira gereksiz bir uyari cumlesi ekleyebilir. Daha buyuk modeller nuansi artirir ama gecikme pahasina.

---

## License / Lisans

Knowledge base notes are original English summaries written while studying an aviation-theory textbook; no text is copied verbatim from the source.

Bilgi tabani notlari, bir ucus teorisi kitabi calisilirken yazilmis ozgun Ingilizce ozetlerdir; kaynaktan hicbir metin birebir kopyalanmamistir.
