"""
Retrieval testi: bir soru alir, TF-IDF benzerligiyle en alakali
chunk'lari SQLite'tan getirir. Modele baglanmadan calisir.
"""
from retrieval import get_top_chunks, load_index

if __name__ == "__main__":
    vectorizer, tfidf_matrix, rows = load_index()

    test_questions = [
    # --- SEVİYE 1: Doğrudan Bilgi Getirme ---
    
    # Beklenen Kaynak: 02-airfoils.md veya 06-flight-performance.md
    "What is a stall and why does it happen?",

    # Beklenen Kaynak: 07-propellers-and-drones.md
    "How does a propeller generate thrust?",

    # Beklenen Kaynak: 08-atmosphere.md
    "What is the primary difference between Indicated Airspeed (IAS) and True Airspeed (TAS), and which airspeed is used for stall speeds?",

    # Beklenen Kaynak: 04-drag.md
    "Can you explain the difference between Parasite Drag and Induced Drag?",

    # Beklenen Kaynak: 01-fundamentals-fluid-mechanics.md
    "According to Bernoulli's Principle, what happens to the static pressure of an incompressible fluid when its velocity increases over the upper surface of a wing?",

    # --- SEVİYE 2: Bağlamsal Sentez ---
    
    # Beklenen Kaynak: 01-fundamentals-fluid-mechanics.md
    "Why do UAVs operate at low Reynolds numbers?",

    # Beklenen Kaynak: 01-fundamentals-fluid-mechanics.md & 04-drag.md
    "How does the boundary layer behavior differ between laminar and turbulent flows, and why do uncrewed aerial vehicles typically operate in low Reynolds number regimes?",

    # Beklenen Kaynak: 03-finite-wing.md
    "What is the Ground Effect, and how does it physically alter the wingtip vortices and induced drag during the landing phase?",

    # Beklenen Kaynak: 05-control-stability.md
    "Explain the difference between Static Stability and Dynamic Stability in flight mechanics.",

    # --- SEVİYE 3: Senaryo ve Mühendislik Uygulaması ---
    
    # Beklenen Kaynak: 05-control-stability.md
    "When configuring a V-tail aerodynamic model for simulation, what hybrid control surfaces are used, and how do they manage both pitch and yaw simultaneously?",

    # Beklenen Kaynak: 07-propellers-and-drones.md
    "We are analyzing the propulsion efficiency of a multirotor drone. According to Blade Element Theory (BET), how is thrust distributed along the span of a single propeller blade, and how does the Advance Ratio (J) affect it?",

    # Beklenen Kaynak: 06-flight-performance.md
    "If an aircraft is flying at a constant angle of attack, how does increasing the wing loading impact the stall speed and the minimum turn radius on a V-n diagram?",

    # --- SEVİYE 4: Sınır Kontrolü ve Kapsam Dışı ---
    
    # Beklenen Kaynak: Genel eşleşmeler / Odak dışı olduğu için görece düşük skor beklenir.
    "What is the airplane and aircraft types?",

    # Beklenen Kaynak: MD dosyalarında supersonic için bilgiler bulunmamakta. Modelin düşük skor getirmesi ve "bilmiyorum" diyebilmesi beklenir.
    "What is the best airfoil for a supersonic jet?"      
    ]

    for q in test_questions:
        print(f"\n{'='*70}\nSORU: {q}\n{'='*70}")
        results = get_top_chunks(q, vectorizer, tfidf_matrix, rows, k=3)
        for r in results:
            print(f"\n[skor: {r['score']:.3f}] {r['source']} -> {r['section']}")
            # chunk'in ilk 150 karakterini goster
            preview = r["text"].split("\n", 1)[-1][:150].replace("\n", " ")
            print(f"    {preview}...")
