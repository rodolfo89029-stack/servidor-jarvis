import os
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# ========================================
# CONFIGURACIÓN
# ========================================

VOICE_ID = "21adf3cda02a4aa88dc593353cc9d715"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


# ========================================
# PERSONALIDAD DE JARVIS
# ========================================

SYSTEM_PROMPT = """
Eres JARVIS, un asistente personal inteligente y futurista.

Hablas siempre en español latino.

Tu personalidad es inteligente, educada, profesional y amigable.

Reglas importantes:
- Responde directamente a lo que dice el usuario.
- No repitas literalmente el mensaje del usuario.
- No copies la pregunta antes de responder.
- No actúes como un eco.
- Mantén conversaciones naturales.
- Recuerda el contexto reciente.
- Llama al usuario señor de manera natural.
- Mantén las respuestas relativamente cortas porque serán convertidas a voz.
- Nunca digas que eres ChatGPT.
- Tu nombre es JARVIS.
"""


# ========================================
# MEMORIA DE CONVERSACIÓN
# ========================================

conversacion = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# ========================================
# PÁGINA PRINCIPAL
# ========================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "status": "online",
        "server": "JARVIS",
        "modelo": OLLAMA_MODEL
    })


# ========================================
# CEREBRO DE JARVIS
# ========================================

def pensar_con_jarvis(texto):

    global conversacion

    print("")
    print("========================================")
    print("JARVIS ESTÁ PENSANDO")
    print("USUARIO:", texto)
    print("========================================")

    conversacion.append({
        "role": "user",
        "content": texto
    })

    # Mantener solamente memoria reciente
    if len(conversacion) > 12:
        conversacion = [
            conversacion[0]
        ] + conversacion[-10:]

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": conversacion,
                "stream": False
            },
            timeout=120
        )

        print("OLLAMA STATUS:", response.status_code)

        if response.status_code != 200:

            print("ERROR OLLAMA:")
            print(response.text)

            return "Lo siento, señor. Tengo un problema con mi sistema de inteligencia."

        data = response.json()

        respuesta = data.get(
            "message",
            {}
        ).get(
            "content",
            ""
        ).strip()

        print("RESPUESTA DE OLLAMA:")
        print(respuesta)

        if not respuesta:

            respuesta = "Lo siento, señor. No he podido generar una respuesta."

        conversacion.append({
            "role": "assistant",
            "content": respuesta
        })

        return respuesta

    except Exception as e:

        print("ERROR CON OLLAMA:")
        print(str(e))

        return "No puedo conectar con mi sistema de inteligencia en este momento, señor."


# ========================================
# TTS + INTELIGENCIA
# ========================================

@app.route("/tts", methods=["POST"])
def tts():

    print("")
    print("========================================")
    print("NUEVA PETICIÓN PARA JARVIS")
    print("========================================")

    # Obtener API Key
    fish_api_key = os.environ.get("FISH_API_KEY")

    print("API KEY PRESENTE:", bool(fish_api_key))

    if not fish_api_key:

        return jsonify({
            "error": "Falta FISH_API_KEY"
        }), 500


    # Obtener mensaje enviado desde Android
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()

    print("TEXTO RECIBIDO:", text)

    if not text:

        return jsonify({
            "error": "Falta el texto"
        }), 400


    # ========================================
    # JARVIS PIENSA LA RESPUESTA
    # ========================================

    respuesta_jarvis = pensar_con_jarvis(text)


    print("")
    print("RESPUESTA FINAL DE JARVIS:")
    print(respuesta_jarvis)


    # ========================================
    # GENERAR VOZ CON FISH AUDIO
    # ========================================

    headers = {
        "Authorization": f"Bearer {fish_api_key}",
        "Content-Type": "application/json",
        "model": "s2.1-pro-free"
    }

    body = {
        "text": respuesta_jarvis,
        "reference_id": VOICE_ID,
        "format": "mp3"
    }

    print("")
    print("GENERANDO VOZ DE JARVIS...")


    try:

        response = requests.post(
            "https://api.fish.audio/v1/tts",
            headers=headers,
            json=body,
            timeout=60
        )

        print("FISH AUDIO STATUS:", response.status_code)

        if response.status_code != 200:

            print("ERROR DE FISH AUDIO:")
            print(response.text[:500])

            return jsonify({
                "error": "Error de Fish Audio",
                "details": response.text
            }), response.status_code


        print("AUDIO RECIBIDO CORRECTAMENTE")
        print("TAMAÑO:", len(response.content), "bytes")
        print("========================================")


        return Response(
            response.content,
            mimetype="audio/mpeg"
        )


    except Exception as e:

        print("ERROR INTERNO:")
        print(str(e))

        return jsonify({
            "error": "Error interno del servidor",
            "details": str(e)
        }), 500


# ========================================
# INICIAR SERVIDOR
# ========================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    print("========================================")
    print("JARVIS SERVER INICIANDO")
    print("========================================")
    print("Puerto:", port)
    print("Modelo IA:", OLLAMA_MODEL)
    print("Fish Audio disponible:", bool(os.environ.get("FISH_API_KEY")))
    print("========================================")

    app.run(
        host="0.0.0.0",
        port=port
    )