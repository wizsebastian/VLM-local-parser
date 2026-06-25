import base64
import sys
import requests

image_path = sys.argv[1] if len(sys.argv) > 1 else "test-image.png"

with open(image_path, "rb") as f:
    img = base64.b64encode(f.read()).decode()

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5vl:7b",
        "prompt": "Extract all the text you can see in this image exactly as it appears",
        "images": [img],
        "stream": False
    }
)

print(response.json()["response"])
