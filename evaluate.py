"""
Degerlendirme.

Varsayilan (hizli, servis gerekmez) - RETRIEVAL:
- Cevaplanabilir sorular: beklenen dosya top-3'te mi? (Hit@3) ve 1. sirada mi? (Top-1)
- Cevaplanamaz sorular: en yuksek skor esik altinda mi? (dogru reddetme)

`python evaluate.py --generate` (Foundry servisi calisir olmali) - ek olarak
UCTAN UCA URETIM:
- Cevaplanabilir: modelin cevabi getirilen baglamda ne kadar "grounded"?
  (cevap kelimelerinin baglamda gecme orani) ve yanlislikla reddetti mi?
- Cevaplanamaz: model gercekten "bilmiyorum" dedi mi?
"""
import argparse
import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from retrieval import (
    RETRIEVAL_MIN_SCORE, context_chunks, get_top_chunks, load_index,
)

# Cevaplanamaz sorular icin skor esigi: uretimdeki ile ayni sabit.
# En yuksek skor bunun altindaysa "sistem emin degil" kabul ediyoruz.
UNANSWERABLE_THRESHOLD = RETRIEVAL_MIN_SCORE

# Uctan uca modda: cevabin kabul edilir sayilmasi icin gereken asgari
# grounding orani (cevap icerik kelimelerinin baglamda gecen kismi).
GROUNDING_MIN = 0.50

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

# Grounding hesabinda sayilmayacak kaynak-atif kaliplari
_CITATION_NOISE = {"source", "section", "referenced", "reference", "sources"}


def _content_words(text):
    """Kucuk harf, >=3 harfli, stop-word olmayan kelimeler kumesi."""
    return {w for w in re.findall(r"[a-z]{3,}", text.lower())
            if w not in ENGLISH_STOP_WORDS}


def is_refusal(answer):
    """Cevabin BASI 'bilmiyorum' mu? (sonda eklenen uyariyi saymaz)"""
    head = answer.strip().lower()[:60]
    return ("don't have that information" in head
            or "do not have that information" in head)


def grounding_score(answer, chunks, question, rows):
    """
    Cevap icerik kelimelerinin ne kadari getirilen baglamda geciyor?
    Baglam = modele verilen baglam (eslesen chunk'lar + komsulari).
    Soruda gecen kelimeler haric tutulur (soruyu tekrar etmek puan olmasin).
    Yaklasik bir olcut: paraphrase / es anlamli sozcuk puani dusurur.
    """
    ctx_text = " ".join(r[3] for r in context_chunks(chunks, rows))
    ctx = _content_words(ctx_text)
    ans = _content_words(answer) - _content_words(question) - _CITATION_NOISE
    if not ans:
        return 1.0
    return len(ans & ctx) / len(ans)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-g", "--generate", action="store_true",
                        help="uctan uca uretimi de calistir (Foundry servisi gerekir)")
    args = parser.parse_args()

    vectorizer, tfidf_matrix, rows = load_index()

    gen = None
    if args.generate:
        from foundry import get_endpoint
        from rag import answer_query
        url, model = get_endpoint()
        gen = {"url": url, "model": model, "answer_query": answer_query}
        print(f"[uctan uca mod: {model} @ {url}]")

    # Retrieval sayaclari
    answerable_total = hit_at_3 = top_1 = 0
    unanswerable_total = correctly_rejected = 0
    # Uretim sayaclari
    grounded_ok = 0
    grounding_sum = 0.0
    false_refusals = 0
    model_rejected = 0

    print("=" * 78)
    print("DEGERLENDIRME RAPORU" + ("  (retrieval + uretim)" if gen else "  (retrieval)"))
    print("=" * 78)

    for item in TEST_SET:
        results = get_top_chunks(item["q"], vectorizer, tfidf_matrix, rows, k=3)
        top_score = results[0]["score"]
        found_sources = [r["source"] for r in results]
        q_short = item["q"][:60] + ("..." if len(item["q"]) > 60 else "")

        answer = None
        if gen:
            answer, _ = gen["answer_query"](
                item["q"], gen["url"], gen["model"], vectorizer, tfidf_matrix, rows
            )

        if item["answerable"]:
            answerable_total += 1
            in_top3 = any(exp in found_sources for exp in item["expected"])
            in_top1 = any(exp == found_sources[0] for exp in item["expected"])
            hit_at_3 += in_top3
            top_1 += in_top1
            mark = "OK " if in_top3 else "MISS"
            rank = " (1. sirada)" if in_top1 else (" (top-3'te)" if in_top3 else "")
            print(f"\n[{mark}] {q_short}")
            print(f"      beklenen: {', '.join(item['expected'])}")
            print(f"      bulunan:  {found_sources[0]} (skor {top_score:.3f}){rank}")

            if gen:
                if is_refusal(answer):
                    false_refusals += 1
                    print("      uretim:   YANLIS REDDETME (cevaplanabilir soruya 'bilmiyorum')")
                else:
                    gscore = grounding_score(answer, results, item["q"], rows)
                    grounding_sum += gscore
                    ok = gscore >= GROUNDING_MIN
                    grounded_ok += ok
                    print(f"      uretim:   grounding {gscore:.2f} "
                          f"({'OK' if ok else 'DUSUK'}, esik {GROUNDING_MIN})")
        else:
            unanswerable_total += 1
            rejected = top_score < UNANSWERABLE_THRESHOLD
            correctly_rejected += rejected
            mark = "OK " if rejected else "ZAYIF"
            print(f"\n[{mark}] {q_short}  (KAPSAM DISI)")
            print(f"      en yuksek skor: {top_score:.3f} "
                  f"(esik {UNANSWERABLE_THRESHOLD} -> "
                  f"{'dogru reddedildi' if rejected else 'esik ustunde, zayif sinyal'})")
            if gen:
                refused = is_refusal(answer)
                model_rejected += refused
                print(f"      uretim:   {'model bilmiyorum dedi (OK)' if refused else 'MODEL CEVAP URETTI (zayif)'}")

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

    if gen:
        scored = answerable_total - false_refusals
        avg = grounding_sum / scored if scored else 0.0
        print("\nURETIM (uctan uca):")
        print(f"  Grounding >= {GROUNDING_MIN}: {grounded_ok}/{scored}")
        print(f"  Ortalama grounding: {avg:.2f}")
        print(f"  Yanlis reddetme (cevaplanabilir -> 'bilmiyorum'): {false_refusals}/{answerable_total}")
        print(f"  Kapsam disi -> model 'bilmiyorum' dedi: {model_rejected}/{unanswerable_total}")
    print("=" * 78)


if __name__ == "__main__":
    main()
