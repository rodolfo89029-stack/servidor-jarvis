import os
import subprocess
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

PRIMARY_MODEL = "llama-3.1-8b-instant"

# Nombre del archivo local y URL de descarga desde Hugging Face
MODEL_FILE = "jarvis-medium.onnx"
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/jarvis/medium/es_ES-jarvis-medium.onnx"

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

def descargar_modelo_si_no_existe():
    """Descarga el modelo ONNX en caso de no estar presente en el servidor."""
    if not os.path.exists(MODEL_FILE):
        print(f"Descargando {MODEL_FILE} desde Hugging Face...")
        res = requests.get(MODEL_URL, stream=True)
        if res.status_code == 200:
            with open(MODEL_FILE, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Descarga del modelo completada exitosamente.")
        else:
            print(f"Error al descargar el modelo. Código: {res.status_code}")

# Ejecutar la descarga previa
descargar_modelo_si_no_existe()


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

    return "Lo siento, señor. Mis sistemas no están respondiendo correctamente."


@app.route("/", methods=["GET"])
def ping():
    return jsonify({"status": "online", "system": "JARVIS OS + Piper TTS"}), 200


@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No se recibió texto."}), 400

    respuesta_texto = pensar_con_jarvis(text)

    output_file = "output.wav"
    cmd = f'echo "{respuesta_texto}" | piper --model {MODEL_FILE} --output_file {output_file}'
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        with open(output_file, "rb") as f:
            audio_bytes = f.read()
        return Response(audio_bytes, mimetype="audio/wav")
    except Exception as e:
        print(f"Error Piper TTS: {e}")
        return jsonify({"error": "Error al sintetizar la voz de JARVIS", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
