#!/usr/bin/env python3
"""
Diagnostico: se conecta por CDP al Chrome/Brave ya abierto y busca en el DOM
los elementos relacionados con el boton de like del chat de un directo TikTok.

Uso:
    python3 buscar_selector.py --puerto 9222
"""

import argparse
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=9222)
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    endpoint = f"http://{args.host}:{args.puerto}"
    print(f"Conectando a {endpoint} ...")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        context = browser.contexts[0]

        # Buscar la pestaña del directo de TikTok
        pagina = None
        for pg in context.pages:
            if "tiktok.com" in (pg.url or "") and "live" in (pg.url or "").lower():
                pagina = pg
                break
        if pagina is None:
            # tomar la ultima pestaña
            pagina = context.pages[-1] if context.pages else None

        if pagina is None:
            print("No hay pestañas abiertas.")
            return

        print(f"Pestaña: {pagina.url}")
        print("=" * 60)

        # 1) Listar todos los data-e2e del documento
        print("\n[1] Atributos data-e2e encontrados en la pagina:")
        data_e2e = pagina.evaluate("""() => {
            const els = document.querySelectorAll('[data-e2e]');
            const out = [];
            els.forEach(e => {
                out.push({
                    e2e: e.getAttribute('data-e2e'),
                    tag: e.tagName.toLowerCase(),
                    text: (e.innerText || '').trim().slice(0, 40),
                    visible: e.offsetParent !== null
                });
            });
            return out;
        }""")
        for item in data_e2e:
            v = "OK " if item["visible"] else "-- "
            print(f"  {v}{item['tag']:12s} data-e2e='{item['e2e']}'  text={item['text']!r}")

        # 2) Buscar elementos que contengan 'like' en data-e2e, aria-label, id o clase
        print("\n[2] Elementos relacionados con 'like' (cualquier atributo):")
        likes = pagina.evaluate("""() => {
            const all = document.querySelectorAll('*');
            const out = [];
            all.forEach(e => {
                const e2e = e.getAttribute('data-e2e') || '';
                const aria = e.getAttribute('aria-label') || '';
                const id = e.id || '';
                const cls = e.className && typeof e.className === 'string' ? e.className : '';
                const hay = [e2e, aria, id, cls].join(' ').toLowerCase();
                if (hay.includes('like') || hay.includes('heart') || hay.includes('fav')) {
                    out.push({
                        tag: e.tagName.toLowerCase(),
                        e2e: e2e,
                        aria: aria,
                        id: id,
                        cls: cls.slice(0, 60),
                        text: (e.innerText || '').trim().slice(0, 30),
                        visible: e.offsetParent !== null
                    });
                }
            });
            return out.slice(0, 40);
        }""")
        for item in likes:
            v = "OK " if item["visible"] else "-- "
            print(f"  {v}{item['tag']:8s} e2e={item['e2e']!r} aria={item['aria']!r} id={item['id']!r} text={item['text']!r}")

        # 3) Iframes presentes (TikTok a veces mete cosas en iframes)
        print("\n[3] Iframes en la pagina:")
        frames = pagina.evaluate("""() => {
            return Array.from(document.querySelectorAll('iframe')).map(f => ({
                src: (f.src || '').slice(0, 80),
                id: f.id,
                name: f.name
            }));
        }""")
        if not frames:
            print("  (sin iframes)")
        for f in frames:
            print(f"  id={f['id']!r} name={f['name']!r} src={f['src']!r}")

        # 4) Estado de carga del chat
        print("\n[4] Elementos de chat / mensaje:")
        chat = pagina.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[data-e2e*=\"chat\" i], [class*=\"chat\" i]').forEach(e => {
                out.push({
                    tag: e.tagName.toLowerCase(),
                    e2e: e.getAttribute('data-e2e') || '',
                    cls: (typeof e.className === 'string' ? e.className : '').slice(0, 50),
                    text: (e.innerText || '').trim().slice(0, 30),
                    visible: e.offsetParent !== null
                });
            });
            return out.slice(0, 25);
        }""")
        for item in chat:
            v = "OK " if item["visible"] else "-- "
            print(f"  {v}{item['tag']:8s} e2e={item['e2e']!r} cls={item['cls']!r} text={item['text']!r}")

        print("\n" + "=" * 60)
        print("Revisa los data-e2e anteriores: el del like deberia parecerse a")
        print("algo con 'like' o 'heart'. Pasa ese valor con --selector.")


if __name__ == "__main__":
    main()
