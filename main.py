"""
Uso:
  python main.py inicializar  -> marca las ofertas actuales como ya vistas (no se publican)
  python main.py preparar     -> descarga ofertas, crea imágenes, texto y la web del enlace en bio
  python main.py publicar     -> sube a Instagram lo preparado (necesita las imágenes ya en GitHub)
"""
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import config
from creatividades import categoria, generar_carrusel
from scraper import filtrar_por_zona, obtener_ofertas

RAIZ = Path(__file__).parent
DATA = RAIZ / "data"
VISTAS = DATA / "vistas.json"
ACTUALES = DATA / "actuales.json"
PENDIENTE = DATA / "pendiente.json"
SALIDA = RAIZ / "output"
DOCS = RAIZ / "docs"


def _leer(ruta, defecto):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else defecto


def _guardar(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _lugar(o):
    if o["provincia"] and o["provincia"].lower() not in o["localidad"].lower():
        return f"{o['localidad']}, {o['provincia']}".strip(", ")
    return o["localidad"] or o["provincia"] or "España"


def texto_publicacion(ofertas, dia: date) -> str:
    cab = f"🩺 Ofertas de empleo sanitario en Madrid · {dia.strftime('%d/%m/%Y')}\n\n"
    empresas = ", ".join(sorted({o["empresa"] for o in ofertas}))
    pie = (
        "✍️ Inscríbete gratis en el portal oficial: empleo.quironsalud.es "
        "(busca la oferta por su nº de referencia)\n\n"
        f"Fuente: portal de empleo de {empresas}.\n\n"
        + " ".join(config.HASHTAGS[:30])
    )
    cuerpo = ""
    for o in ofertas:
        bloque = f"▪️ {o['titulo']}\n📍 {_lugar(o)} · Ref. {o['id']}\n\n"
        if len(cab) + len(cuerpo) + len(bloque) + len(pie) > 2150:
            cuerpo += "…y más en el enlace de la bio\n\n"
            break
        cuerpo += bloque
    return cab + cuerpo + pie


def generar_web(ofertas):
    """Página para el enlace en bio (GitHub Pages sirve la carpeta /docs)."""
    hoy = date.today()
    filas = []
    for o in ofertas:
        try:
            nueva = (hoy - date.fromisoformat(o["fecha"])).days <= 3
            fecha = date.fromisoformat(o["fecha"]).strftime("%d/%m/%Y")
        except ValueError:
            nueva, fecha = False, ""
        e = lambda s: html.escape(str(s))
        filas.append(
            f'<a class="o" href="{e(o["url"])}" target="_blank" rel="noopener" '
            f'data-t="{e((o["titulo"] + " " + _lugar(o) + " " + o["id"]).lower())}">'
            f'<span class="cat">{e(categoria(o["titulo"]))}</span>'
            f'{"<span class=nueva>NUEVA</span>" if nueva else ""}'
            f'<b>{e(o["titulo"])}</b><small>📍 {e(_lugar(o))} · {e(o["empresa"])} · {fecha} · Ref. {e(o["id"])}</small></a>'
        )
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(config.NOMBRE_CUENTA)} · Ofertas</title>
<style>
body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f3f5fa;color:#0f1b3d}}
header{{background:#0f1b3d;color:#fff;padding:24px 18px}}h1{{margin:0;font-size:22px}}
header p{{margin:6px 0 0;opacity:.8;font-size:14px}}main{{max-width:720px;margin:auto;padding:14px}}
input{{width:100%;box-sizing:border-box;padding:14px;border-radius:12px;border:1px solid #ccd;font-size:16px;margin-bottom:12px}}
.o{{display:block;background:#fff;border-radius:14px;padding:14px 16px;margin-bottom:10px;text-decoration:none;color:inherit;box-shadow:0 1px 3px #0001}}
.o b{{display:block;margin:6px 0 4px;font-size:16px}}.o small{{color:#667}}
.cat,.nueva{{font-size:11px;font-weight:700;padding:3px 8px;border-radius:20px;background:#ffe3df;color:#c73b2b;margin-right:6px}}
.nueva{{background:#0f1b3d;color:#fff}}footer{{font-size:12px;color:#889;text-align:center;padding:20px}}
</style></head><body>
<header><h1>{html.escape(config.NOMBRE_CUENTA)}</h1><p>{len(ofertas)} ofertas · actualizado {hoy.strftime('%d/%m/%Y')} · pulsa una oferta para inscribirte</p></header>
<main><input id="q" placeholder="Busca por puesto, ciudad o nº de referencia…" oninput="f()">
{''.join(filas)}
</main><footer>Al pulsar una oferta accedes directamente a su página oficial de inscripción de Quirónsalud.</footer>
<script>function f(){{const q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('.o').forEach(a=>a.style.display=a.dataset.t.includes(q)?'':'none')}}</script>
</body></html>"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(pagina, encoding="utf-8")


def limpiar_imagenes_antiguas():
    limite = date.today() - timedelta(days=config.DIAS_CONSERVAR_IMAGENES)
    for carpeta in SALIDA.glob("*"):
        try:
            if carpeta.is_dir() and date.fromisoformat(carpeta.name) < limite:
                shutil.rmtree(carpeta)
        except ValueError:
            pass


def cmd_inicializar():
    ofertas = filtrar_por_zona(obtener_ofertas())
    vistas = _leer(VISTAS, {})
    ahora = datetime.now().isoformat(timespec="seconds")
    for o in ofertas:
        vistas.setdefault(o["id"], {**o, "estado": "omitida", "cuando": ahora})
    _guardar(VISTAS, vistas)
    _guardar(ACTUALES, ofertas)
    generar_web(ofertas)
    print(f"Inicializado: {len(ofertas)} ofertas marcadas como vistas.")


def cmd_preparar():
    hoy = date.today()
    ofertas = filtrar_por_zona(obtener_ofertas())
    print(f"Ofertas activas en el portal (tras filtro de zona): {len(ofertas)}")
    _guardar(ACTUALES, ofertas)
    generar_web(ofertas)
    limpiar_imagenes_antiguas()

    vistas = _leer(VISTAS, {})
    nuevas = [o for o in ofertas if o["id"] not in vistas]
    print(f"Ofertas sin publicar: {len(nuevas)}")
    if len(nuevas) < config.MIN_OFERTAS_PARA_PUBLICAR:
        PENDIENTE.unlink(missing_ok=True)
        print("No hay suficientes ofertas nuevas hoy.")
        return
    lote = nuevas[: config.MAX_OFERTAS_POR_DIA]
    carpeta = SALIDA / hoy.isoformat()
    if carpeta.exists():
        # Vaciar en vez de borrar la carpeta: OneDrive puede bloquear el rmdir
        for f in carpeta.glob("*"):
            f.unlink()
    rutas = generar_carrusel(lote, hoy, carpeta)
    _guardar(PENDIENTE, {
        "fecha": hoy.isoformat(),
        "ofertas": lote,
        "imagenes": [str(r.relative_to(RAIZ)).replace("\\", "/") for r in rutas],
        "texto": texto_publicacion(lote, hoy),
    })
    print(f"Preparado carrusel con {len(lote)} ofertas en {carpeta}")


def cmd_publicar():
    pendiente = _leer(PENDIENTE, None)
    if not pendiente:
        print("Nada pendiente de publicar.")
        return
    if not (os.environ.get("IG_USER_ID") and os.environ.get("IG_ACCESS_TOKEN")):
        print("MODO PRUEBA: sin credenciales de Instagram. Imágenes y texto generados, no se publica.")
        print(pendiente["texto"])
        return

    from instagram import publicar_carrusel, publicar_historias

    repo = os.environ["GITHUB_REPOSITORY"]  # lo pone GitHub Actions: usuario/repositorio
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip()
    urls = [f"https://raw.githubusercontent.com/{repo}/{sha}/{p}" for p in pendiente["imagenes"]]
    id_post = publicar_carrusel(urls, pendiente["texto"])
    print(f"Publicado en Instagram: {id_post}")

    # También subimos todo el carrusel a Historias (sin sticker de enlace: la API no lo permite).
    try:
        ids_hist = publicar_historias(urls)
        print(f"Historias publicadas: {len(ids_hist)}")
    except Exception as e:
        print(f"Aviso: no se pudieron publicar las historias ({e}). El feed sí se publicó.")

    vistas = _leer(VISTAS, {})
    ahora = datetime.now().isoformat(timespec="seconds")
    for o in pendiente["ofertas"]:
        vistas[o["id"]] = {**o, "estado": "publicada", "cuando": ahora, "post": id_post}
    _guardar(VISTAS, vistas)
    PENDIENTE.unlink()


if __name__ == "__main__":
    comandos = {"inicializar": cmd_inicializar, "preparar": cmd_preparar, "publicar": cmd_publicar}
    if len(sys.argv) != 2 or sys.argv[1] not in comandos:
        print(__doc__)
        sys.exit(1)
    comandos[sys.argv[1]]()
