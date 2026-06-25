# Análisis de seguridad — VLM Local Parser

Contexto evaluado: servidor Flask que actúa como proxy hacia un Ollama local, pensado para ejecutarse dentro de una red privada (p. ej. Tailscale). A continuación las vulnerabilidades ordenadas por severidad.

> **Estado:** los puntos #1, #2, #3, #5 y #9 están **mitigados** (ver notas ✅ en cada uno). Pendientes/aceptados como riesgo: #4 (dev server) y #6 (CSRF); #7 y #8 quedan mitigados al enlazar el servicio solo a la interfaz Tailscale.

---

## 🔴 Alta

### 1. El servidor escucha en `0.0.0.0` sin autenticación ✅ mitigado
`server.py` → `host` se toma de `VLM_HOST` con default `100.73.140.30` (solo interfaz Tailscale).

Enlazar a `0.0.0.0` expone el puerto 5000 en **todas** las interfaces (Tailscale y LAN/WiFi). Como `/parse` no exige credenciales, cualquier cliente que alcance el puerto puede usar la GPU del host: consumir VRAM, encolar inferencias o degradar el servicio. En una red compartida o pública, cualquier dispositivo del segmento puede llegar al endpoint.

**Mitigación:**
- Para uso en la misma máquina: `host="127.0.0.1"`.
- Para acceso vía Tailscale: enlazar solo a la IP de la interfaz Tailscale (`100.x.x.x`) en lugar de `0.0.0.0`.
- Añadir autenticación mínima (un token en el header `Authorization`) cuando más de un dispositivo deba acceder.

### 2. Sin límite de tamaño de payload → DoS / agotamiento de memoria ✅ mitigado
`server.py` → `app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024`.

Un cliente puede enviar un base64 arbitrariamente grande. Flask lo carga completo en memoria antes de procesarlo; varias peticiones grandes en paralelo agotan RAM/VRAM. Tampoco se valida que el contenido sea realmente una imagen: cualquier blob base64 se reenvía tal cual a Ollama.

**Mitigación:**
```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
```
Además, conviene validar el tipo/decodificación antes de reenviar a Ollama.

---

## 🟠 Media

### 3. Sin `timeout` en la llamada a Ollama → worker colgado ✅ mitigado
`server.py` → `requests.post(..., timeout=120)` con manejo de `RequestException` → 502.

Si Ollama se cuelga o tarda indefinidamente, la petición de Flask queda bloqueada esperando. Varias peticiones así agotan los workers (el servidor de desarrollo de Flask atiende pocas conexiones). Es un vector de DoS amplificado.

**Mitigación:** usar `requests.post(..., timeout=120)` y manejar `requests.Timeout`.

### 4. Servidor de desarrollo de Werkzeug en uso "real"
`app.run(...)` levanta el servidor de desarrollo de Flask, no apto para exposición: no maneja bien la concurrencia ni cargas hostiles, y si se activa `debug=True`, la consola de Werkzeug permite **ejecución remota de código** a quien acceda. Actualmente está en `debug=False` (✅), pero conviene dejarlo documentado.

**Mitigación:** al exponerlo más allá de localhost, servirlo detrás de `gunicorn`/`waitress` y nunca activar `debug` en una interfaz alcanzable.

### 5. Respuestas de error sin manejar → 500 / posible fuga de stack ✅ mitigado
- `request.get_json()` devuelve `None` si el body no es JSON → `None.get("image")` lanza `AttributeError` → 500.
- `response.json()["response"]` falla con `KeyError` si Ollama responde otra forma o está caído.

Sin `response.raise_for_status()` ni `try/except`, el servicio se cae con entradas inesperadas. Con `debug=False` el traceback no se filtra al cliente (✅).

**Mitigación:** validar `data`, usar `silent=True` en `get_json`, comprobar el status de Ollama y envolver en `try/except`.

---

## 🟡 Baja / Endurecimiento

### 6. CSRF / petición cross-origin hacia `/parse`
Una web maliciosa puede disparar un `POST` a `http://<host>:5000/parse` desde el navegador de un usuario. El preflight de CORS impide **leer** la respuesta, pero la petición **sí llega** y consume recursos. Riesgo bajo (no hay datos sensibles que robar), pero suma al vector de DoS si la IP es alcanzable.

**Mitigación:** autenticación por token (resuelve esto y el punto #1 a la vez).

### 7. Tráfico en texto plano fuera de Tailscale
Dentro de Tailscale el tráfico va cifrado (WireGuard ✅). Al enlazar en `0.0.0.0`, el acceso por LAN es **HTTP plano**: las imágenes (que pueden contener información sensible) viajan sin cifrar. Limitar el bind a la interfaz Tailscale (punto #1) elimina este riesgo.

### 8. Servir archivos por ruta dinámica
Servir archivos en función de un parámetro controlado por el cliente abre la puerta a *path traversal*. Mientras los nombres servidos estén fijos/hardcodeados el riesgo no aplica; es un recordatorio para futuras rutas de archivos.

### 9. Higiene del repo ✅ mitigado
- `test.py` lee la ruta desde `sys.argv` (default `test-image.png`), sin rutas absolutas personales.
- Se añadió `requirements.txt` (`flask`, `requests`).
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

Para un despliegue estrictamente local en una sola máquina, **resolver el #1 (bind a localhost) y el #2 (límite de tamaño) elimina la mayor parte del riesgo real.**
