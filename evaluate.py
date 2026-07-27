"""
Retrieval degerlendirme: etiketli test sorulariyla retrieval kalitesini olcer.
- Cevaplanabilir sorular: beklenen dosya top-3'te mi? (Hit@3) ve 1. sirada mi? (Top-1)
- Cevaplanamaz sorular: en yuksek skor esik altinda mi? (dogru reddetme)
"""
import sqlite3
import pickle
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "knowledge.db"
VECTORIZER_PATH = "vectorizer.pkl"
MATRIX_PATH = "tfidf_matrix.pkl"

# Cevaplanamaz sorular icin skor esigi:
# en yuksek skor bunun altindaysa "sistem emin degil" kabul ediyoruz
UNANSWERABLE_THRESHOLD = 0.25

# Etiketli test seti: her soru + beklenen kaynak dosya(lar)
# answerable=False olanlar bilgi tabaninda YOK, dusuk skor bekliyoruz
TEST_SET = [
    # SEVIYE 1: Dogrudan bilgi getirme
    {"q": "What is a stall and why does it happen?",
     "expected": ["02-airfoils.md", "06-flight-performance.md"], "answerable": True},
    {"q": "How does a propeller generate thrust?",
     "expected": ["07-propellers-and-drones.md"], "answerable": True},
    {"q": "What is the primary difference between Indicated Airspeed (IAS) and True Airspeed (TAS), and which airspeed is used for stall speeds?",
     "expected": ["08-atmosphere.md"], "answerable": True},
    {"q": "Can you explain the difference between Parasite Drag and Induced Drag?",
     "expected": ["04-drag.md"], "answerable": True},
    {"q": "According to Bernoulli's Principle, what happens to the static pressure of an incompressible fluid when its velocity increases over the upper surface of a wing?",
     "expected": ["01-fundamentals-fluid-mechanics.md"], "answerable": True},
    # SEVIYE 2: Baglamsal sentez
    {"q": "Why do UAVs operate at low Reynolds numbers?",
     "expected": ["01-fundamentals-fluid-mechanics.md"], "answerable": True},
    {"q": "How does the boundary layer behavior differ between laminar and turbulent flows, and why do uncrewed aerial vehicles typically operate in low Reynolds number regimes?",
     "expected": ["01-fundamentals-fluid-mechanics.md"], "answerable": True},
    {"q": "What is the Ground Effect, and how does it physically alter the wingtip vortices and induced drag during the landing phase?",
     "expected": ["03-finite-wing.md"], "answerable": True},
    {"q": "Explain the difference between Static Stability and Dynamic Stability in flight mechanics.",
     "expected": ["05-control-stability.md"], "answerable": True},
    # SEVIYE 3: Senaryo ve muhendislik uygulamasi
    {"q": "When configuring a V-tail aerodynamic model for simulation, what hybrid control surfaces are used, and how do they manage both pitch and yaw simultaneously?",
     "expected": ["05-control-stability.md"], "answerable": True},
    {"q": "We are analyzing the propulsion efficiency of a multirotor drone. According to Blade Element Theory (BET), how is thrust distributed along the span of a single propeller blade, and how does the Advance Ratio (J) affect it?",
     "expected": ["07-propellers-and-drones.md"], "answerable": True},
    {"q": "If an aircraft is flying at a constant angle of attack, how does increasing the wing loading impact the stall speed and the minimum turn radius on a V-n diagram?",
     "expected": ["06-flight-performance.md"], "answerable": True},
    # SEVIYE 4: Sinir kontrolu ve kapsam disi
    {"q": "What is the airplane and aircraft types?",
     "expected": [], "answerable": False},
    {"q": "What is the best airfoil for a supersonic jet?",
     "expected": [], "answerable": False},
]


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
        {"score": float(scores[i]), "source": rows[i][1], "section": rows[i][2]}
        for i in top_idx
    ]


def main():
    vectorizer, tfidf_matrix, rows = load_index()

    # Sayaclar
    answerable_total = 0
    hit_at_3 = 0
    top_1 = 0
    unanswerable_total = 0
    correctly_rejected = 0

    print("=" * 78)
    print("RETRIEVAL DEGERLENDIRME RAPORU")
    print("=" * 78)

    for item in TEST_SET:
        results = get_top_chunks(item["q"], vectorizer, tfidf_matrix, rows, k=3)
        top_score = results[0]["score"]
        found_sources = [r["source"] for r in results]

        # soruyu kisalt (ekranda okunur olsun)
        q_short = item["q"][:60] + ("..." if len(item["q"]) > 60 else "")

        if item["answerable"]:
            answerable_total += 1
            # beklenen dosyalardan herhangi biri top-3'te mi?
            in_top3 = any(exp in found_sources for exp in item["expected"])
            in_top1 = any(exp == found_sources[0] for exp in item["expected"])
            if in_top3:
                hit_at_3 += 1
            if in_top1:
                top_1 += 1
            mark = "OK " if in_top3 else "MISS"
            rank = " (1. sirada)" if in_top1 else (" (top-3'te)" if in_top3 else "")
            print(f"\n[{mark}] {q_short}")
            print(f"      beklenen: {', '.join(item['expected'])}")
            print(f"      bulunan:  {found_sources[0]} (skor {top_score:.3f}){rank}")
        else:
            unanswerable_total += 1
            # kapsam disi: en yuksek skor esik altinda mi?
            rejected = top_score < UNANSWERABLE_THRESHOLD
            if rejected:
                correctly_rejected += 1
            mark = "OK " if rejected else "ZAYIF"
            print(f"\n[{mark}] {q_short}  (KAPSAM DISI)")
            print(f"      en yuksek skor: {top_score:.3f} "
                  f"(esik {UNANSWERABLE_THRESHOLD} -> "
                  f"{'dogru reddedildi' if rejected else 'esik ustunde, zayif sinyal'})")

    # Ozet
    print("\n" + "=" * 78)
    print("OZET")
    print("=" * 78)
    print(f"Cevaplanabilir sorular: {answerable_total}")
    print(f"  Hit@3 (dogru dosya ilk 3'te): {hit_at_3}/{answerable_total} "
          f"= %{100*hit_at_3//answerable_total}")
    print(f"  Top-1 (dogru dosya 1. sirada): {top_1}/{answerable_total} "
          f"= %{100*top_1//answerable_total}")
    print(f"Kapsam disi sorular: {unanswerable_total}")
    print(f"  Dogru reddedilen (skor < {UNANSWERABLE_THRESHOLD}): "
          f"{correctly_rejected}/{unanswerable_total}")
    print("=" * 78)


if __name__ == "__main__":
    main()
