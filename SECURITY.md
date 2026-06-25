# Análisis de seguridad — VLM Local Parser

Contexto evaluado: servidor Flask corriendo en tu homelab, accesible dentro de tu red privada (Tailscale). A continuación las vulnerabilidades ordenadas por severidad.

> **Estado:** los puntos #1, #2, #3, #5 y #9 fueron **mitigados** (ver notas ✅ en cada uno). Pendientes/aceptados como riesgo: #4 (dev server), #6 (CSRF), #7 y #8 (mitigados al enlazar solo a Tailscale).

---

## 🔴 Alta

### 1. El servidor escucha en `0.0.0.0` sin autenticación ✅ mitigado
`server.py` → ahora `host` viene de `VLM_HOST` con default `100.73.140.30` (solo interfaz Tailscale).

`0.0.0.0` expone el puerto 5000 en **todas** las interfaces: Tailscale **y** tu LAN/WiFi. Como `/parse` no pide ninguna credencial, **cualquiera que alcance ese puerto puede usar tu GPU** (consumir VRAM, hacer cola de inferencias, o tumbarte el servicio). Si te conectas a un WiFi público o compartido, cualquier dispositivo de esa red puede llegar.

**Mitigación:**
- Si solo lo usas tú en la misma máquina: `host="127.0.0.1"`.
- Si lo usas vía Tailscale: enlázalo solo a la IP de la interfaz Tailscale (`100.x.x.x`) en vez de `0.0.0.0`.
- Añade auth mínima (un token en header `Authorization`) si más de un dispositivo debe acceder.

### 2. Sin límite de tamaño de payload → DoS / agotamiento de memoria ✅ mitigado
`server.py` → `app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024`.

Un cliente puede mandar un base64 enorme. Flask lo carga entero en memoria antes de procesarlo. Con varias peticiones grandes en paralelo agotas RAM/VRAM. No hay validación de que el contenido sea realmente una imagen: cualquier blob base64 se reenvía tal cual a Ollama.

**Mitigación:**
```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
```
Y valida el tipo/decodificación antes de reenviar a Ollama.

---

## 🟠 Media

### 3. Sin `timeout` en la llamada a Ollama → worker colgado ✅ mitigado
`server.py` → `requests.post(..., timeout=120)` con manejo de `RequestException` → 502.

Si Ollama se cuelga o tarda indefinidamente, la petición de Flask queda bloqueada esperando. Varias peticiones así agotan los workers (el servidor de desarrollo de Flask atiende pocas conexiones). Es un vector de DoS amplificado.

**Mitigación:** `requests.post(..., timeout=120)` y maneja `requests.Timeout`.

### 4. Servidor de desarrollo de Werkzeug en uso "real"
`app.run(...)` levanta el servidor de desarrollo de Flask, no apto para exposición. No maneja concurrencia ni cargas hostiles bien, y si algún día cambias `debug=True`, la consola de Werkzeug permite **ejecución remota de código** a quien acceda. Hoy está en `debug=False` (✅), pero déjalo documentado.

**Mitigación:** si lo expones más allá de localhost, ponlo detrás de `gunicorn`/`waitress` y nunca actives `debug` en una interfaz alcanzable.

### 5. Respuestas de error sin manejar → 500 / posible fuga de stack ✅ mitigado
- `server.py:14` `request.get_json()` devuelve `None` si el body no es JSON → `None.get("image")` lanza `AttributeError` → 500.
- `server.py:33` `response.json()["response"]` revienta con `KeyError` si Ollama responde otra forma o está caído.

No hay `response.raise_for_status()` ni `try/except`. Con `debug=False` no se filtra el traceback al cliente (✅), pero el servicio se cae con entradas inesperadas.

**Mitigación:** valida `data`, usa `silent=True` en `get_json`, comprueba el status de Ollama y envuelve en `try/except`.

---

## 🟡 Baja / Endurecimiento

### 6. CSRF / petición cross-origin hacia `/parse`
Una web maliciosa que visites podría disparar un `POST` a `http://<tu-ip>:5000/parse` desde tu navegador. El preflight de CORS impide que **lean** la respuesta, pero la petición **sí llega** y consume recursos. Riesgo bajo porque no hay datos sensibles que robar, pero suma al vector de DoS si la IP es alcanzable.

**Mitigación:** auth por token (resuelve esto y el punto 1 a la vez).

### 7. Tráfico en texto plano fuera de Tailscale
Dentro de Tailscale el tráfico va cifrado (WireGuard ✅). Pero como escuchas en `0.0.0.0`, el acceso por LAN es **HTTP plano**: las imágenes (que pueden contener info sensible de tus capturas) viajan sin cifrar. Resolver el punto 1 (no exponer en LAN) elimina esto.

### 8. `send_from_directory(".", "index.html")`
Hoy es seguro porque el nombre está hardcodeado. Si en el futuro sirves archivos según parámetro del usuario, cuida el *path traversal*. Solo es un recordatorio.

### 9. Higiene del repo ✅ mitigado
- `test.py` ahora lee la ruta de `sys.argv` (default `test-image.png`), sin ruta personal.
- Añadido `requirements.txt` (`flask`, `requests`).
- `.gitignore` ignora `*.png` (✅, evita subir capturas con datos por accidente).

---

## Resumen de prioridades

| # | Problema | Acción mínima |
|---|----------|---------------|
| 1 | `0.0.0.0` sin auth | Bind a `127.0.0.1`/IP Tailscale **o** token de auth |
| 2 | Sin límite de tamaño | `MAX_CONTENT_LENGTH` + validar imagen |
| 3 | Sin timeout a Ollama | `timeout=` + manejar excepción |
| 4 | Dev server | `gunicorn`/`waitress` si se expone; nunca `debug=True` expuesto |
| 5 | Errores no manejados | `try/except` + validación de entrada |

Para uso estrictamente personal en una sola máquina, **resolver el #1 (bind a localhost) y el #2 (límite de tamaño) elimina la mayor parte del riesgo real.**
