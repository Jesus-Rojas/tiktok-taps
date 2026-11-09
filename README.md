# TikTok Taps - Automatización de clicks

Dos scripts en Python para automatizar clicks:

| Script           | Cómo elige dónde clickear                | Mejor para                         |
|------------------|------------------------------------------|------------------------------------|
| `auto_clicker.py`| Coordenadas (x, y) de pantalla            | Cualquier ventana, app genérica    |
| `like_bot.py`    | Selector CSS del elemento (DOM) en Brave | Dar likes en un directo de TikTok  |

> **Atajo:** `like_bot.py` se puede correr en Docker (recomendado, no ensucia tu
> máquina). Ve a la sección **Docker** más abajo.

---

## like_bot.py — clicks por selector en Brave

Hace click en bucle en el botón de like del chat de un directo de TikTok,
identificado por:

```
[data-e2e="room-chat-like-btn"]
```

(Puedes cambiarlo con `--selector`.)

Funciona en dos modos:

- **MODO A (recomendado):** se conecta a tu Brave ya abierto por CDP. Mantiene
  tu sesión y login tal cual. No necesita descargar ningún navegador.
- **MODO B:** lanza un Brave nuevo con perfil persistente (te logueas una vez).

### Argumentos

| Argumento      | Descripción                                            | Por defecto                          |
|----------------|--------------------------------------------------------|--------------------------------------|
| `--puerto`      | MODO A: puerto CDP de Brave ya abierto                 | —                                    |
| `--host`        | MODO A: host del CDP (Docker: `host.docker.internal` o `localhost` con network_mode host) | `localhost` |
| `--url`         | MODO B: URL del directo a abrir                         | —                                    |
| `--selector`    | Selector CSS del elemento a clickear                   | `[data-e2e='room-chat-like-btn']`    |
| `--intervalo`   | Segundos entre clicks (`-i`)                          | 1.0                                  |
| `--veces`       | Total de clicks. 0 = infinito (`-n`)                    | 0                                    |
| `--espera`      | Segundos máx. a que aparezca el elemento               | 30                                   |
| `--executable`  | MODO B: ruta del ejecutable de Brave                  | autodetectado                        |
| `--headless`    | MODO B: Brave sin ventana (no recomendado para TikTok)  | no                                   |
| `--perfil`      | MODO B: carpeta del perfil persistente                | `./perfil_brave`                     |

`--puerto` y `--url` son mutuamente excluyentes. Detener: `Ctrl+C`.

---

## Docker (recomendado para like_bot)

No instala nada en tu máquina: todo corre en un contenedor que sólo trae el
paquete `playwright` y se conecta por CDP a tu Brave del host (MODO A).

### 1) Arranca tu Brave con el puerto de depuración

Cierra Brave y ábrelo así (en tu máquina, no en Docker):

```bash
brave-browser --remote-debugging-port=9222
```

En esa ventana abre el directo de TikTok donde quieres dar likes (con tu login normal).

### 2) Construye la imagen (una sola vez)

```bash
docker build -t tiktok-like-bot .
# o con compose:
docker compose build
```

### 3) Lanza el bot

```bash
# Infinitos likes cada 1s
docker run --rm --network host tiktok-like-bot --puerto 9222 -i 1.0

# 200 likes cada 0.5s
docker run --rm --network host tiktok-like-bot --puerto 9222 -i 0.5 -n 200

# Con compose (usa el comando por defecto: --puerto 9222 --intervalo 1.0)
docker compose up

# Con compose, pasando tus propios argumentos:
docker compose run --rm like-bot --puerto 9222 -i 0.5 -n 200
```

`--network host` hace que `localhost:9222` del contenedor apunte al Brave de tu
máquina. Si no puedes usar network host, lanza con
`--add-host=host.docker.internal:host-gateway` y añade `--host host.docker.internal`.

### Notas

- Si el botón desaparece un instante, el script reespera y reintenta en vez de morir.
- TikTok puede limitar la cantidad de likes por tiempo; usa un intervalo razonable.
- Logs/builds van a la carpeta `.tmp/` del workspace.

---

## Instalación local (alternativa a Docker)

```bash
pip install -r requirements.txt
# solo si vas a usar el MODO B (lanzar Brave nuevo):
playwright install chromium
```

### MODO A local

```bash
brave-browser --remote-debugging-port=9222   # abre Brave con el puerto
python3 like_bot.py --puerto 9222 -i 1.0
```

### MODO B local

```bash
python3 like_bot.py --url "https://www.tiktok.com/@usuario/live" -i 1.0
```

---

## auto_clicker.py — clicks por coordenadas (genérico)

Clicks en una posición fija (o en el cursor) cada X segundos. Sirve para
cualquier ventana, no solo navegadores.

```bash
# Click en (500, 300) cada 2s, infinitos
python3 auto_clicker.py --x 500 --y 300 --intervalo 2.0

# 50 clicks en (960, 540) cada 1.5s
python3 auto_clicker.py --x 960 --y 540 -i 1.5 -n 50

# Click donde esté el mouse cada 0.8s
python3 auto_clicker.py --intervalo 0.8
```

| Argumento        | Descripción                              | Por defecto |
|------------------|------------------------------------------|-------------|
| `--x` / `--y`    | Coordenada del click (juntos o ninguno)  | cursor      |
| `--intervalo`    | Segundos entre clicks (`-i`)             | 1.0         |
| `--veces`        | Total de clicks. 0 = infinito (`-n`)    | 0           |
| `--boton`        | `izquierdo` / `derecho`                   | izquierdo   |
| `--cuenta-atras` | Segundos de espera antes de empezar      | 5           |

Detener: `ESC` o `Ctrl+C`. Requiere `pyautogui` y `pynput`
(`sudo apt install python3-tk python3-dev` en Linux).

Para saber la coordenada de un punto, mueve el mouse ahí y ejecuta:
```bash
python3 -c "import pyautogui; print(pyautogui.position())"
```
