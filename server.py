import os
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# ========================================
# CONFIGURACIÓN Y MODELOS
# ========================================

VOICE_ID = "21adf3cda02a4aa88dc593353cc9d715"

# Modelo principal ultrarrápido
PRIMARY_MODEL = "llama-3.1-8b-instant"


# ========================================
# PERSONALIDAD DE JARVIS
# ========================================

SYSTEM_PROMPT = """
Eres JARVIS, un asistente personal inteligente, amigable y futurista.

Reglas de respuesta:
- Hablas siempre en español latino fluido y natural.
- Dirígete al usuario como 'señor' de forma natural y respetuosa.
- Mantén respuestas concisas y directas (1 a 3 oraciones), ideales para sintetización de voz.
- No repitas la pregunta del usuario ni actúes como eco.
- Nunca te identifiques como ChatGPT ni como un modelo de lenguaje genérico. Tu nombre es JARVIS.
"""

conversacion = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# ========================================
# CEREBRO OPTIMIZADO (GROQ + FALLBACK)
# ========================================

def pensar_con_jarvis(texto):
    global conversacion

    print("\n" + "="*40)
    print(f"JARVIS PROCESANDO: {texto}")
    print("="*40)

    # Añadir mensaje del usuario
    conversacion.append({"role": "user", "content": texto})

    # Mantener memoria reciente eficiente (últimos 8 mensajes)
    if len(conversacion) > 10:
        conversacion = [conversacion[0]] + conversacion[-8:]

    # 1. Intentar con Groq API
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
                print(f"RESPUESTA (Groq): {respuesta}")
                return respuesta
            else:
                print(f"Error Groq HTTP {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Excepción en Groq: {e}")

    # 2. Respaldo opcional con Gemini API (Si configuras GEMINI_API_KEY)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            body = {"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\nUsuario: {texto}"}]}]}
            res = requests.post(url, json=body, timeout=10)
            if res.status_code == 200:
                respuesta = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                conversacion.append({"role": "assistant", "content": respuesta})
                print(f"RESPUESTA (Gemini Fallback): {respuesta}")
                return respuesta
        except Exception as e:
            print(f"Excepción en Gemini: {e}")

    # Respuesta de contingencia si no hay claves configuradas o fallan las APIs
    return "Lo siento, señor. Mis sistemas de inteligencia no están respondiendo correctamente en este momento."


# ========================================
# ENDPOINTS Y RUTAS HTTP
# ========================================

@app.route("/", methods=["GET"])
def ping():
    return jsonify({
        "status": "online",
        "system": "JARVIS OS",
        "engine": "Groq + Fish Audio"
    }), 200


@app.route("/tts", methods=["POST"])
def tts():
    # Detección flexible de API Key de Fish Audio
    fish_key = os.environ.get("FISH_API_KEY") or os.environ.get("FISH_AUDIO_API_KEY")
    
    if not fish_key:
        print("ERROR: Clave de Fish Audio no encontrada.")
        return jsonify({"error": "Falta la variable FISH_API_KEY en Railway."}), 500

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No se recibió texto."}), 400

    # Obtener respuesta del cerebro
    respuesta_texto = pensar_con_jarvis(text)

    # Generar audio con Fish Audio
    headers = {
        "Authorization": f"Bearer {fish_key}",
        "Content-Type": "application/json"
    }

    body = {
        "text": respuesta_texto,
        "reference_id": VOICE_ID,
        "format": "mp3",
        "latency": "normal"
    }

    try:
        response = requests.post(
            "https://api.fish.audio/v1/tts",
            headers=headers,
            json=body,
            timeout=30
        )

        if response.status_code != 200:
            print(f"Error Fish Audio [{response.status_code}]: {response.text}")
            return jsonify({
                "error": "Error al sintetizar voz con Fish Audio",
                "details": response.text
            }), response.status_code

        print(f"Audio generado con éxito ({len(response.content)} bytes)")
        return Response(response.content, mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error interno en sintetizador: {e}")
        return jsonify({"error": "Error en el servidor de voz", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
