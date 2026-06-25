import base64
import requests

with open("/home/wizsebastian/projects/VLM-parse/test-image.png", "rb") as f:
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
