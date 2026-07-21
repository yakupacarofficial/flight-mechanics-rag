import openai
import requests

# Foundry Local, çalışan servisin gerçek adresini bu sabit uçtan bildirir.
# (Servisin portu her restart'ta değişse de burası sabit kalır.)
def get_endpoint():
    # Önce bilinen son portu, sonra Foundry'nin varsayılan keşif portunu dene
    for port in (50034, 5273):
        try:
            url = f"http://127.0.0.1:{port}/v1"
            models = requests.get(f"{url}/models", timeout=2).json()
            model_id = models["data"][0]["id"]
            return url, model_id
        except Exception:
            continue
    raise RuntimeError("Foundry servisi bulunamadi. 'foundry service status' calisiyor mu?")

BASE_URL, MODEL = get_endpoint()
print(f"[servis: {BASE_URL} | model: {MODEL}]")

client = openai.OpenAI(base_url=BASE_URL, api_key="not-needed")

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "In one sentence, what is lift in aerodynamics?"}
    ],
)

print(response.choices[0].message.content)
