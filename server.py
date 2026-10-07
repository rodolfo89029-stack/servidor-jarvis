import os
import requests
from flask import Flask, request, Response, jsonify, send_file

app = Flask(__name__)

PRIMARY_MODEL = "llama-3.1-8b-instant"

# Reemplaza con tu API Key y tu Model ID de Fish Audio
FISH_AUDIO_API_KEY = os.environ.get("sk-fish-i__1odWiayUHBgLsHz8DFA-O97NrRUvyLoCWw2W9IWU", "")
FISH_MODEL_ID = os.environ.get("a728b3e3bda3425799f0555792b463ff", "")  # ID de la voz de JARVIS en Fish Audio

SYSTEM_PROMPT = """
Eres JARVIS, el asistente personal inteligente, amigable y futurista de Iron Man.

Reglas de respuesta:
- Hablas siempre en español fluido y natural.
- Dirígete al usuario como 'señor' de forma natural y respetuosa.
- Mantén respuestas concisas y directas (1 a 3 oraciones), ideales para sintetización de voz.
- Tu nombre es JARVIS.
"""

conversacion = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def pensar_con_jarvis(texto):
    global conversacion

    print(f"\nJARVIS PROCESANDO: {texto}")
    conversacion.append({"role": "user", "content": texto})

    if len(conversacion) > 10:
        conversacion = [conversacion[0]] + conversacion[-8:]

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": PRIMARY_MODEL,
                "messages": conversacion,
                "temperature": 0.6,
                "max_tokens": 250
            }

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=10
            )

            if res.status_code == 200:
                respuesta = res.json()["choices"][0]["message"]["content"].strip()
                conversacion.append({"role": "assistant", "content": respuesta})
                return respuesta
        except Exception as e:
            print(f"Error Groq: {e}")

    return "Lo siento, señor. Mis sistemas de inteligencia no están respondiendo correctamente."


@app.route("/", methods=["GET"])
def index():
    return send_file("index.html")


@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No se recibió texto."}), 400

    respuesta_texto = pensar_con_jarvis(text)

    # Si tienes configurada la API de Fish Audio
    if FISH_AUDIO_API_KEY and FISH_MODEL_ID:
        try:
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "text": respuesta_texto,
                "reference_id": FISH_MODEL_ID,
                "format": "mp3"
            }

            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                return Response(res.content, mimetype="audio/mpeg")
            else:
                print(f"Error Fish Audio status: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Error petición Fish Audio: {e}")

    return jsonify({"error": "No se pudo generar el audio con Fish Audio. Revisa las variables en Railway."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
