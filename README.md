# VLM Local Parser 🖼️→📝

Extrae texto de cualquier *screenshot* usando un **Vision Language Model (VLM)** corriendo **100% local** en tu GPU. Pega una captura con `Cmd+V` y obtén el texto en ~8 segundos, sin enviar tus datos a ninguna nube.

> Nació de un dolor real: cada captura que mandaba a Claude/Codex/Gemini para que me explicara una interfaz me costaba ~1,500 tokens. Multiplicado por decenas de imágenes al mes, eso devoraba mi cuota por hora y me dejaba sin tokens para lo que de verdad importaba: generar código. La solución fue dejar de pagar por "ver" y mover esa tarea a mi propio homelab de IA.
>
> 📖 Historia completa: *"Why stop gaming saved my tokens: Construyendo mi propio AI Lab Local"*

## ¿Cómo funciona?

```
Navegador (paste/drag imagen)
      │  POST /parse  { image: base64 }
      ▼
server.py  (Flask, puerto 5000)
      │  POST http://localhost:11434/api/generate
      ▼
Ollama  →  qwen2.5vl:7b  (VLM en tu GPU)
      │
      ▼
  Texto extraído  →  textarea + botón "Copy"
```

Un OCR tradicional solo saca texto plano. Un **VLM** *entiende* la imagen (interfaces, diagramas, contexto), por eso da resultados mucho más útiles. Y `qwen2.5vl:7b` cabe en 12 GB de VRAM (probado en una RTX 4070).

## Requisitos

- **Python 3.x** (deps en `requirements.txt`: `flask`, `requests`)
- **[Ollama](https://ollama.com/)** corriendo localmente
- El modelo VLM descargado:
  ```sh
  ollama pull qwen2.5vl:7b
  ```
- Una GPU con ~12 GB de VRAM (funciona en CPU, pero lento)

## Instalación y uso

```sh
# 1. Clona el repo
git clone https://github.com/wizsebastian/VLM-local-parser.git
cd VLM-local-parser

# 2. Entorno virtual + dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Asegúrate de que Ollama esté corriendo y el modelo descargado
ollama pull qwen2.5vl:7b

# 4. Levanta el servidor
python server.py

# 5. Abre http://100.73.140.30:5000 (vía Tailscale) y pega un screenshot con Cmd+V
```

Por defecto el servidor escucha **solo en la interfaz Tailscale** (`100.73.140.30`), así que únicamente los dispositivos de tu tailnet pueden acceder. Puedes cambiarlo con variables de entorno:

| Variable      | Default                              | Descripción                          |
|---------------|--------------------------------------|--------------------------------------|
| `VLM_HOST`    | `100.73.140.30`                      | Interfaz donde escucha Flask         |
| `VLM_PORT`    | `5000`                               | Puerto                               |
| `OLLAMA_URL`  | `http://localhost:11434/api/generate`| Endpoint de Ollama                   |
| `VLM_MODEL`   | `qwen2.5vl:7b`                       | Modelo VLM a usar                    |

Ejemplo (solo en tu máquina): `VLM_HOST=127.0.0.1 python server.py`

### Prueba rápida por CLI

`test.py` envía una imagen directo a Ollama (sin pasar por Flask):

```sh
python test.py ruta/a/imagen.png   # o deja test-image.png en el directorio
```

## Endpoints

| Método | Ruta      | Descripción                                              |
|--------|-----------|----------------------------------------------------------|
| `GET`  | `/`       | Sirve la interfaz web (`index.html`).                    |
| `POST` | `/parse`  | Recibe `{ "image": "<base64 o data-URL>" }`, devuelve `{ "text": "..." }`. |

## Stack

- **Backend:** Flask + `requests` (proxy ligero hacia Ollama)
- **Frontend:** HTML/CSS/JS vanilla, sin build
- **Modelo:** `qwen2.5vl:7b` vía Ollama

## ⚠️ Seguridad

Este proyecto está pensado para uso **personal en una red privada** (ej. detrás de Tailscale en tu homelab). **No lo expongas a internet tal cual**: el endpoint `/parse` no tiene autenticación ni límites de tamaño y el servidor escucha en `0.0.0.0`. Ver `SECURITY.md` para el detalle y cómo endurecerlo.

---

*Construido desde la fricción de los rate limits hasta tener una API local de visión por computadora. — Luis Sebastian Vasquez. Usa la IA con responsabilidad.*
