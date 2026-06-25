from flask import Flask, request, jsonify, send_from_directory
import base64
import requests
import os

app = Flask(__name__)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json()
    image_b64 = data.get("image")

    if not image_b64:
        return jsonify({"error": "No image provided"}), 400

    if "," in image_b64:
        image_b64 = image_b64.split(",")[1]

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5vl:7b",
            "prompt": "Extract all the text you can see in this image exactly as it appears. Return only the extracted text, no explanations.",
            "images": [image_b64],
            "stream": False
        }
    )

    text = response.json()["response"]
    return jsonify({"text": text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
