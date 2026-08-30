"""
Foundry Local baglanti yardimcisi.

Foundry Local servisi her baslatmada RASTGELE bir port secer. Bu modul
portu su sirayla bulur:
  1. FOUNDRY_ENDPOINT / FOUNDRY_PORT ortam degiskeni (elle override)
  2. 'foundry service status' ciktisindaki guncel port (otoritatif kaynak)
  3. Bilinen portlar (servis/CLI yoksa son care)

Bulunan her aday, /v1/models ile dogrulanir; ilk cevap veren kazanir.

Kullanim:
    from foundry import get_endpoint
    base_url, model = get_endpoint()
    # -> ("http://127.0.0.1:55845/v1", "Phi-3.5-mini-instruct-generic-gpu:2")
"""
import os
import re
import shutil
import subprocess

import requests

# Servis de CLI de yoksa denenecek portlar (gecmiste gorulen degerler)
FALLBACK_PORTS = (5273, 50034, 49947, 55845, 55913, 55333, 54901)

# Chat modeli secimi: id'sinde bu ifade gecen ilk model tercih edilir
PREFERRED_MODEL = "phi-3.5"


def _candidate_ports():
    """Denenecek portlari oncelik sirasiyla, tekrarsiz dondurur."""
    ports = []

    # 1. Elle override: "http://127.0.0.1:9000/v1" ya da duz "9000".
    #    Son ":" parcasinin basindaki sayiyi al (IP oktetleriyle karismasin).
    env = os.environ.get("FOUNDRY_ENDPOINT") or os.environ.get("FOUNDRY_PORT")
    if env:
        m = re.match(r"(\d{2,5})", env.rsplit(":", 1)[-1].strip())
        if m:
            ports.append(int(m.group(1)))

    # 2. 'foundry service status' -> "... running on http://127.0.0.1:PORT/..."
    if shutil.which("foundry"):
        try:
            out = subprocess.run(
                ["foundry", "service", "status"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            m = re.search(r"https?://[\d.]+:(\d{2,5})", out)
            if m:
                ports.append(int(m.group(1)))
        except Exception:
            pass

    # 3. Bilinen portlar
    ports.extend(FALLBACK_PORTS)

    seen = set()
    return [p for p in ports if not (p in seen or seen.add(p))]


def _pick_model(models_json):
    ids = [m["id"] for m in models_json.get("data", [])]
    for mid in ids:
        if PREFERRED_MODEL in mid.lower():
            return mid
    if ids:
        return ids[0]
    return "phi-3.5-mini"  # servis istek gelince yukler


def get_endpoint(timeout=2):
    """
    Calisan Foundry servisinin OpenAI-uyumlu taban URL'sini ve chat
    modelini dondurur: (base_url, model_id).
    Hicbir aday cevap vermezse RuntimeError firlatir.
    """
    last_err = None
    for port in _candidate_ports():
        url = f"http://127.0.0.1:{port}/v1"
        try:
            resp = requests.get(f"{url}/models", timeout=timeout)
            resp.raise_for_status()
            return url, _pick_model(resp.json())
        except Exception as e:  # noqa: BLE001 - bir sonraki portu dene
            last_err = e
    raise RuntimeError(
        "Foundry servisi bulunamadi. Terminalde 'foundry service start' "
        f"calistigindan emin olun. (son hata: {last_err})"
    )


def chat(base_url, model, messages, temperature=0.2, max_tokens=400, timeout=120):
    """
    Foundry Local'a tek parca (non-stream) sohbet istegi gonderir ve
    modelin cevap metnini dondurur.

    openai kutuphanesi yerine dogrudan requests kullanilir: govde tek
    seferde yollanir, boylece Foundry'nin "request body timed out" (500)
    hatasi olusmaz. trust_env=False ile yerel istekte proxy ortam
    degiskenleri yoksayilir.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    sess = requests.Session()
    sess.trust_env = False
    resp = sess.post(f"{base_url}/chat/completions", json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Foundry {resp.status_code}: {resp.text[:500]}")
    return resp.json()["choices"][0]["message"]["content"]
