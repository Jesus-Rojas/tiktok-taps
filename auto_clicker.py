#!/usr/bin/env python3
"""
Auto Clicker - Clicks por coordenadas.

Da clicks automaticos en una posicion especifica (o en la posicion actual
del mouse) cada cierto intervalo de tiempo, de forma indefinida o un numero
finito de veces. Generico: sirve para cualquier ventana de cualquier app.

    python3 auto_clicker.py --x 500 --y 300 --intervalo 2.0
    python3 auto_clicker.py --intervalo 0.8            # usa posicion del mouse
    python3 auto_clicker.py --x 960 --y 540 --veces 50

Atajos:
    ESC        : Detener el script inmediatamente.
    Ctrl + C   : Detener desde la terminal.

    pip install pyautogui pynput
"""

import argparse
import sys
import time

try:
    import pyautogui
except ImportError:
    print("Falta la libreria 'pyautogui'. Instala con:  pip install pyautogui")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("Falta la libreria 'pynput'. Instala con:  pip install pynput")
    sys.exit(1)


# Desactivamos el FAILSAFE (que lanza excepcion si el mouse topa la esquina)
# para que no interrumpa el bucle por movimientos puntuales.
pyautogui.FAILSAFE = False

# Bandera global para detener el script desde el listener de teclado.
_detener = False


def _al_pulsar_tecla(tecla):
    """Listener de teclado: detiene el script al pulsar ESC."""
    global _detener
    if tecla == keyboard.Key.esc:
        _detener = True
        return False  # detiene el listener


def _cuenta_atras(segundos):
    """Muestra una cuenta atras para dar tiempo a cambiar de ventana."""
    for i in range(segundos, 0, -1):
        sys.stdout.write(f"\rIniciando en {i} seg... (ESC para cancelar)")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()


def hacer_clicks(x, y, intervalo, veces, boton, pre_cuenta):
    """Ejecuta el bucle de clicks automaticos por coordenadas."""
    global _detener
    _detener = False

    listener = keyboard.Listener(on_press=_al_pulsar_tecla)
    listener.start()

    print("=" * 50)
    print("AUTO CLICKER (por coordenadas)")
    print(f"  Posicion : ({x}, {y})" if x is not None else "  Posicion : cursor actual")
    print(f"  Intervalo: {intervalo} s")
    print(f"  Boton     : {boton}")
    print(f"  Veces     : {'infinitas (ESC para parar)' if veces == 0 else veces}")
    print("  Detener   : tecla ESC / Ctrl+C")
    print("=" * 50)

    if pre_cuenta > 0:
        _cuenta_atras(pre_cuenta)

    boton_pyautogui = "right" if boton == "derecho" else "left"
    n = 0
    try:
        while True:
            if _detener:
                print("\n[Detenido por el usuario]")
                break

            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, button=boton_pyautogui)
            else:
                pyautogui.click(button=boton_pyautogui)

            n += 1
            pos = f"({x}, {y})" if x is not None else "cursor"
            print(f"  Click #{n} en {pos}")

            if veces > 0 and n >= veces:
                print(f"\n[Completado: {n} clicks]")
                break

            time.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[Detenido con Ctrl+C]")
    finally:
        listener.stop()


def parsear_args():
    parser = argparse.ArgumentParser(
        description="Automatiza clicks en una posicion cada X segundos.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--x", type=int, default=None,
                        help="Coordenada X. Si se omite, usa la posicion del mouse.")
    parser.add_argument("--y", type=int, default=None,
                        help="Coordenada Y. Si se omite, usa la posicion del mouse.")
    parser.add_argument("--intervalo", "-i", type=float, default=1.0,
                        help="Segundos entre cada click (por defecto: 1.0).")
    parser.add_argument("--veces", "-n", type=int, default=0,
                        help="Numero total de clicks. 0 = infinito (por defecto: 0).")
    parser.add_argument("--boton", choices=["izquierdo", "derecho"], default="izquierdo",
                        help="Boton a pulsar (por defecto: izquierdo).")
    parser.add_argument("--cuenta-atras", "-c", type=int, default=5,
                        help="Segundos de espera antes de empezar (por defecto: 5).")
    return parser.parse_args()


def main():
    args = parsear_args()
    if (args.x is None) != (args.y is None):
        print("Error: --x y --y deben indicarse juntos (o ninguno de los dos).")
        sys.exit(1)
    if args.intervalo <= 0:
        print("Error: el intervalo debe ser mayor que 0.")
        sys.exit(1)

    hacer_clicks(
        x=args.x, y=args.y, intervalo=args.intervalo, veces=args.veces,
        boton=args.boton, pre_cuenta=args.cuenta_atras,
    )


if __name__ == "__main__":
    main()
