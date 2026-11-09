#!/usr/bin/env python3
"""
Like Bot - Clicks por selector en Brave (TikTok Live).

Hace click en un elemento de la pagina identificado por su selector CSS,
en bucle, cada X segundos. Pensado para automatizar el boton de "like"
del chat de un directo de TikTok:

    selector por defecto: [data-e2e="room-chat-like-btn"]

Brave es Chromium, asi que funciona con Playwright.

---- DOS MODOS DE USO ----

MODO A) Conectar a tu Brave YA ABIERTO (mantiene tu sesion y login).
  Arranca Brave con el puerto de depuracion CDP:

      brave-browser --remote-debugging-port=9222

  Abre el directo de TikTok en esa ventana y ejecuta:

      python3 like_bot.py --puerto 9222 --intervalo 1.0

  En Docker (network_mode host) vale lo mismo; sin network_mode host usa:
      python3 like_bot.py --puerto 9222 --host host.docker.internal -i 1.0

MODO B) Lanzar un Brave nuevo con perfil persistente (te logueas una vez).
  El script lanza Brave con su propio perfil guardado en ./perfil_brave.

      python3 like_bot.py --url "https://www.tiktok.com/@usuario/live" --intervalo 1.0

---- EJEMPLOS ----

  python3 like_bot.py --puerto 9222 -i 0.5          # infinitos likes cada 0.5s
  python3 like_bot.py --url "https://www.tiktok.com/@u/live" -i 1.2 -n 100
  python3 like_bot.py --puerto 9222 --selector "[data-e2e='otro-btn']" -i 2

Detener: Ctrl + C  (o cerrar la terminal).
"""

import argparse
import os
import shutil
import sys
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Falta la libreria 'playwright'. Instala con:")
    print("    pip install playwright")
    print("Y, solo si lanzas un Brave nuevo (modo B), descarga el driver:")
    print("    playwright install chromium")
    sys.exit(1)


# Rutas habituales del ejecutable de Brave en Linux.
_RUTAS_BRAVE = [
    "/usr/bin/brave-browser",
    "/usr/bin/brave",
    "/opt/brave.com/brave/brave",
    "/snap/bin/brave",
]


def buscar_brave():
    """Devuelve la ruta del ejecutable de Brave si la encuentra, si no None."""
    for ruta in _RUTAS_BRAVE:
        if shutil.which(ruta) or os.path.isfile(ruta):
            return ruta
    return None


def _solo_visible(selector):
    """Anade ':visible' a un selector CSS para ignorar elementos ocultos.

    TikTok suele renderizar dos elementos con el mismo data-e2e: una copia
    oculta (plantilla/SSR) y el real visible. Sin este filtro, .first pilla el
    oculto y el click falla en bucle.
    """
    s = selector.strip()
    # 'text=', 'xpath=', 'role=' no son selectores CSS; los dejamos igual.
    if s.startswith(("text=", "xpath=", "role=")):
        return s
    return f"{s}:visible"


def bucle_clicks(pagina, selector, espera, intervalo, veces):
    """Busca el elemento y hace click en bucle hasta parar o completar `veces`."""
    # Filtramos solo el elemento visible (TikTok duplica el boton: uno oculto).
    selector_visible = _solo_visible(selector)
    print("Esperando el elemento:", selector)
    try:
        pagina.wait_for_selector(selector_visible, timeout=espera * 1000)
    except PWTimeout:
        print(f"No se encontro el selector '{selector}' (visible) en {espera}s.")
        print("Comprueba que el directo y el chat estan abiertos, que tienes")
        print("sesion iniciada en esa ventana y que el selector es correcto.")
        print("(Si el directo tarda en cargar, sube el tiempo: --espera 60)")
        return

    print("Elemento encontrado. Empezando a dar likes...  (Ctrl+C para parar)")
    print("=" * 50)

    n = 0
    try:
        while True:
            try:
                pagina.locator(selector_visible).first.click(timeout=5000)
            except Exception as e:
                # El elemento puede desaparecer un instante; reintentamos.
                print(f"  (click fallido: {type(e).__name__}; reintentando...)")
                try:
                    pagina.wait_for_selector(selector_visible, timeout=espera * 1000)
                except PWTimeout:
                    print("El elemento desaparecio y no volvio. Saliendo.")
                    break
                continue

            n += 1
            print(f"  Like #{n}")
            if veces > 0 and n >= veces:
                print(f"\n[Completado: {n} likes]")
                break
            time.sleep(intervalo)

    except KeyboardInterrupt:
        print(f"\n[Detenido. Likes enviados: {n}]")


def elegir_pestaña(context, url):
    """Elige la pestaña que coincide con --url (si se dio) o la ultima abierta."""
    if url:
        objetivo = url.replace("https://", "").replace("http://", "").rstrip("/")
        for pg in context.pages:
            if objetivo in (pg.url or ""):
                return pg
    return context.pages[-1] if context.pages else None


def abrir_por_cdp(puerto, url, selector, espera, intervalo, veces, host="localhost"):
    """MODO A: se conecta a un Brave ya abierto via CDP."""
    endpoint = f"http://{host}:{puerto}"
    print(f"Conectando a Brave en {endpoint} ...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint)
        except Exception as e:
            print(f"No se pudo conectar a Brave en {endpoint}.")
            print(f"  Arrancalo con:  brave-browser --remote-debugging-port={puerto}")
            print(f"  (Detalle: {type(e).__name__})")
            return

        if not browser.contexts:
            print("No se encontro ningun contexto en Brave. Abre una pestaña y reintenta.")
            return
        context = browser.contexts[0]

        pagina = elegir_pestaña(context, url)
        if pagina is None:
            print("No hay pestañas abiertas. Abre el directo de TikTok y reintenta.")
            return

        print(f"Pestaña seleccionada: {pagina.url}")
        if url and url not in (pagina.url or ""):
            print(f"  (no coincide con --url {url}; usando esta pestaña de todas formas)")

        bucle_clicks(pagina, selector, espera, intervalo, veces)


def lanzar_brave(url, selector, espera, intervalo, veces, executable, headless, user_data_dir):
    """MODO B: lanza un Brave nuevo con perfil persistente."""
    exe = executable or buscar_brave()
    if not exe:
        print("No se encontro el ejecutable de Brave.")
        print("Indica la ruta con --executable /ruta/a/brave-browser")
        sys.exit(1)
    print(f"Lanzando Brave: {exe}")
    print(f"Perfil guardado en: {user_data_dir}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            executable_path=exe,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )
        pagina = context.pages[0] if context.pages else context.new_page()

        print(f"Abriendo {url} ...")
        pagina.goto(url, wait_until="domcontentloaded", timeout=60000)

        bucle_clicks(pagina, selector, espera, intervalo, veces)
        context.close()


def parsear_args():
    parser = argparse.ArgumentParser(
        description="Bot de likes por selector CSS en Brave (TikTok Live).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--puerto", type=int, default=None,
                        help="MODO A: puerto CDP de Brave ya abierto (ej: 9222).")
    parser.add_argument("--host", default="localhost",
                        help="MODO A: host del CDP (en Docker usa host.docker.internal\n"
                             "o 'localhost' si usas network_mode host).")
    parser.add_argument("--url", default=None,
                        help="MODO B: URL del directo de TikTok a abrir.")
    parser.add_argument("--selector", default="[data-e2e='room-chat-like-btn']",
                        help="Selector CSS del elemento a clickear (por defecto: like de TikTok Live).")
    parser.add_argument("--intervalo", "-i", type=float, default=1.0,
                        help="Segundos entre cada click (por defecto: 1.0).")
    parser.add_argument("--veces", "-n", type=int, default=0,
                        help="Numero total de clicks. 0 = infinito (por defecto: 0).")
    parser.add_argument("--espera", type=int, default=30,
                        help="Segundos maximos de espera a que aparezca el elemento (por defecto: 30).")
    parser.add_argument("--executable", default=None,
                        help="MODO B: ruta del ejecutable de Brave (autodetectado por defecto).")
    parser.add_argument("--headless", action="store_true",
                        help="MODO B: lanza Brave sin ventana (no recomendado para TikTok).")
    parser.add_argument("--perfil", default="./perfil_brave",
                        help="MODO B: carpeta del perfil persistente (por defecto: ./perfil_brave).")
    return parser.parse_args()


def main():
    args = parsear_args()

    if args.puerto and args.url:
        print("Error: usa --puerto (MODO A) o --url (MODO B), no ambos a la vez.")
        sys.exit(1)
    if not args.puerto and not args.url:
        print("Error: indica --puerto (Brave ya abierto) o --url (lanzar Brave nuevo).")
        sys.exit(1)
    if args.intervalo <= 0:
        print("Error: el intervalo debe ser mayor que 0.")
        sys.exit(1)

    if args.puerto:
        abrir_por_cdp(args.puerto, args.url, args.selector,
                     args.espera, args.intervalo, args.veces, args.host)
    else:
        lanzar_brave(args.url, args.selector, args.espera,
                     args.intervalo, args.veces,
                     args.executable, args.headless, args.perfil)


if __name__ == "__main__":
    main()
