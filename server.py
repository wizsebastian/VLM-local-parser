from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("VLM_MODEL", "qwen2.5vl:7b")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json(silent=True)
    if not data or not data.get("image"):
        return jsonify({"error": "No image provided"}), 400

    image_b64 = data["image"]
    if "," in image_b64:
        image_b64 = image_b64.split(",")[1]

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": "Extract all the text you can see in this image exactly as it appears. Return only the extracted text, no explanations.",
                "images": [image_b64],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        text = response.json()["response"]
    except (requests.RequestException, KeyError, ValueError):
        return jsonify({"error": "VLM backend unavailable"}), 502

    return jsonify({"text": text})

def banner(host, port):
    # "Ember on Espresso" — warm amber accent, soft coral heart (256-color ANSI)
    ember, heart, dim, reset = "\033[38;5;215m", "\033[38;5;209m", "\033[2m", "\033[0m"
    print(f"""
{ember}  ◢ VLM PARSE{reset}  {dim}— local document extraction{reset}
{dim}  ─────────────────────────────────────────{reset}
  Serving on  {ember}http://{host}:{port}{reset}
  Model       {MODEL}
{dim}  ─────────────────────────────────────────{reset}
  Made with {heart}❤{reset}  by {ember}https://wizsebastian.com{reset}
""")


if __name__ == "__main__":
    host = os.environ.get("VLM_HOST", "100.73.140.30")
    port = int(os.environ.get("VLM_PORT", "5000"))
    banner(host, port)
    app.run(host=host, port=port, debug=False)
