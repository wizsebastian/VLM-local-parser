# VLM Local Parser 🖼️→📝

Extract text from any *screenshot* using a **Vision Language Model (VLM)** running **100% locally** on your GPU. Paste a capture with `Cmd+V` and get the text back in ~8 seconds, without sending your data to any cloud.

> It was born from a real pain point: every screenshot I sent to Claude/Codex/Gemini to explain an interface cost me ~1,500 tokens. Multiplied by dozens of images a month, that devoured my hourly quota and left me without tokens for what really mattered: generating code. The fix was to stop paying to "see" and move that task to my own AI homelab.
>
> 📖 Full story: *"Why stop gaming saved my tokens: Building my own local AI Lab"*

## How it works

```
Browser (paste/drag image)
      │  POST /parse  { image: base64 }
      ▼
server.py  (Flask, port 5000)
      │  POST http://localhost:11434/api/generate
      ▼
Ollama  →  qwen2.5vl:7b  (VLM on your GPU)
      │
      ▼
  Extracted text  →  textarea + "Copy" button
```

A traditional OCR only pulls plain text. A **VLM** *understands* the image (interfaces, diagrams, context), which is why it gives far more useful results. And `qwen2.5vl:7b` fits in 12 GB of VRAM (tested on an RTX 4070).

## Requirements

- **Python 3.x** (deps in `requirements.txt`: `flask`, `requests`)
- **[Ollama](https://ollama.com/)** running locally
- The VLM model pulled:
  ```sh
  ollama pull qwen2.5vl:7b
  ```
- A GPU with ~12 GB of VRAM (works on CPU, but slow)

## Install & run

```sh
# 1. Clone the repo
git clone https://github.com/wizsebastian/VLM-local-parser.git
cd VLM-local-parser

# 2. Virtual environment + dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Make sure Ollama is running and the model is pulled
ollama pull qwen2.5vl:7b

# 4. Start the server
python server.py

# 5. Open http://100.73.140.30:5000 (via Tailscale) and paste a screenshot with Cmd+V
```

By default the server listens **only on the Tailscale interface** (`100.73.140.30`), so only devices on your tailnet can reach it. You can change this with environment variables:

| Variable      | Default                              | Description                          |
|---------------|--------------------------------------|--------------------------------------|
| `VLM_HOST`    | `100.73.140.30`                      | Interface Flask binds to             |
| `VLM_PORT`    | `5000`                               | Port                                 |
| `OLLAMA_URL`  | `http://localhost:11434/api/generate`| Ollama endpoint                      |
| `VLM_MODEL`   | `qwen2.5vl:7b`                       | VLM model to use                     |

Example (local machine only): `VLM_HOST=127.0.0.1 python server.py`

### Quick CLI test

`test.py` sends an image straight to Ollama (bypassing Flask):

```sh
python test.py path/to/image.png   # or drop a test-image.png in the directory
```

## Endpoints

| Method | Route     | Description                                              |
|--------|-----------|----------------------------------------------------------|
| `GET`  | `/`       | Serves the web UI (`templates/index.html`).              |
| `POST` | `/parse`  | Takes `{ "image": "<base64 or data-URL>" }`, returns `{ "text": "..." }`. |

## Stack

- **Backend:** Flask + `requests` (thin proxy to Ollama)
- **Frontend:** Jinja2 templates (`templates/`) + Tailwind CSS (standalone Play CDN, no Node build) + vanilla JS (`static/`). Single responsive view — no separate React project.
- **Model:** `qwen2.5vl:7b` via Ollama

```
VLM-local-parser/
├── server.py             # Flask: serves the page + /parse proxy
├── templates/index.html  # Jinja view, Tailwind utility classes (responsive)
├── static/
│   ├── css/style.css     # bespoke effects (glassmorphism, glow, scan line)
│   └── js/app.js         # clipboard / drag & drop / fetch logic
└── requirements.txt
```

## ⚠️ Security

This project is meant for **personal use on a private network** (e.g. behind Tailscale in your homelab). The server is hardened to bind to the Tailscale interface and enforces a request-size limit, an Ollama timeout, and error handling. See `SECURITY.md` for the full assessment and the remaining hardening notes before exposing it any wider.

---

*Built from the friction of rate limits all the way to a local computer-vision API. — Luis Sebastian Vasquez. Use AI responsibly.*

🌐 [wizsebastian.com](https://wizsebastian.com)
