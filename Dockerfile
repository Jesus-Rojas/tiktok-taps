# Imagen minima para el like-bot: solo necesita el paquete `playwright`
# porque se conecta por CDP al Brave que ya corre en el host (MODO A).
# No hace falta descargar Chromium (playwright install).
FROM python:3.11-slim

WORKDIR /app

# Instalamos solo la libreria (sin descargar navegadores: usamos CDP).
RUN pip install --no-cache-dir playwright==1.44.0

COPY like_bot.py .

# El ENTRYPOINT es el script; los argumentos se pasan al hacer docker run/compose.
ENTRYPOINT ["python3", "like_bot.py"]
