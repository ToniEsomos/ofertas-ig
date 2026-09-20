"""
Genera las imágenes (1080x1350, formato 4:5 de Instagram) para el carrusel diario.
"""
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

ANCHO, ALTO = 1080, 1350
DIR_FUENTES = Path(__file__).parent / "fonts"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CATEGORIAS = [  # el orden importa: se usa la primera coincidencia
    ("PRÁCTICAS", ["prácticas", "practicas"]),
    ("TCAE / AUXILIAR", ["auxiliar de enfermer", "auxiliar enfermer", "aux. enfermer", "tcae",
                         "técnico en cuidados", "auxiliar de enfermeria"]),
    ("ENFERMERÍA", ["enfermer", "matron", "matrona"]),
    ("FISIOTERAPIA", ["fisioterap"]),
    ("FARMACIA", ["farmac"]),
    ("MEDICINA", ["médic", "medic", "facultativ", "especialista", "licenciado en medicina",
                  "ginecólog", "urólog", "oncólog", "digestivo", "anestesi", "jefe/a de servicio",
                  "jefe/a servicio", "radiofísic", "radiofisic"]),
    ("TÉCNICO SANITARIO", ["radiodiagnóstico", "técnico de farmacia", "higienista", "laboratorio"]),
    ("SERVICIOS", ["celador", "limpi", "cocin", "friegaplatos", "restauración", "mantenimiento",
                   "auxiliar de servicios", "electromedicina", "infraestructuras"]),
    ("GESTIÓN Y OFICINA", ["administrativ", "admisión", "contabilidad", "nóminas", "laborales",
                           "abogado", "controller", "compras", "analista", "comercial",
                           "atención al paciente", "teleoperador", "agente", "informador",
                           "coordinador", "gestor", "técnico/a", "aplicaciones it", "prevención"]),
]


def categoria(titulo: str) -> str:
    # Primero se mira el puesto (antes de " - " o "("), luego el título completo
    puesto = titulo.split(" - ")[0].split("(")[0].lower()
    for texto in (puesto, titulo.lower()):
        for nombre, claves in CATEGORIAS:
            if any(c in texto for c in claves):
                return nombre
    return "EMPLEO"


def separar_titulo(titulo: str) -> tuple[str, str]:
    """'Enfermero/a UCI - Hospital X' -> ('Enfermero/a UCI', 'Hospital X')."""
    if " - " in titulo:
        puesto, detalle = titulo.split(" - ", 1)
    elif "(" in titulo and titulo.rstrip().endswith(")"):
        puesto, detalle = titulo.split("(", 1)
        detalle = detalle.rstrip(") ")
    else:
        return titulo, ""
    puesto, detalle = puesto.strip(), detalle.strip()
    # "MOVILIDAD INTERNA - Auxiliar ..." : el primer trozo no es el puesto
    if puesto.isupper() and len(puesto.split()) <= 3 and not detalle.isupper():
        return titulo, ""
    if len(puesto) < 4:
        return titulo, ""
    return puesto, detalle


def fecha_larga(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _fuente(peso: str, tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(DIR_FUENTES / f"Montserrat-{peso}.ttf"), tam)


def _envolver(draw, texto, fuente, ancho_max):
    """Parte el texto en líneas que caben en ancho_max (px)."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
            continue
        if actual:
            lineas.append(actual)
        # palabra más larga que la línea: se corta
        while draw.textlength(palabra, font=fuente) > ancho_max:
            corte = len(palabra)
            while corte > 1 and draw.textlength(palabra[:corte] + "-", font=fuente) > ancho_max:
                corte -= 1
            lineas.append(palabra[:corte] + "-")
            palabra = palabra[corte:]
        actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def _ajustar_titulo(draw, texto, ancho_max, alto_max, tam_max=84, tam_min=44):
    for tam in range(tam_max, tam_min - 1, -2):
        f = _fuente("ExtraBold", tam)
        lineas = _envolver(draw, texto, f, ancho_max)
        interlineado = int(tam * 1.18)
        if len(lineas) * interlineado <= alto_max:
            return f, lineas, interlineado
    f = _fuente("ExtraBold", tam_min)
    lineas = _envolver(draw, texto, f, ancho_max)
    interlineado = int(tam_min * 1.18)
    max_lineas = max(1, alto_max // interlineado)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        lineas[-1] = lineas[-1].rstrip(".,-") + "…"
    return f, lineas, interlineado


def _decoracion(img):
    """Círculos decorativos semitransparentes."""
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    r, g, b = config.COLOR_ACENTO
    d.ellipse((ANCHO - 330, -260, ANCHO + 250, 320), fill=(r, g, b, 60))
    d.ellipse((-220, ALTO - 260, 200, ALTO + 160), fill=(255, 255, 255, 18))
    img.alpha_composite(capa)


def _cabecera(draw, derecha: str = ""):
    f = _fuente("Bold", 30)
    draw.text((80, 70), config.NOMBRE_CUENTA.upper(), font=f, fill=config.COLOR_TEXTO)
    draw.rectangle((80, 116, 150, 122), fill=config.COLOR_ACENTO)
    if derecha:
        fd = _fuente("SemiBold", 28)
        w = draw.textlength(derecha, font=fd)
        draw.text((ANCHO - 80 - w, 72), derecha, font=fd, fill=config.COLOR_TEXTO)


def _pie(draw):
    f = _fuente("Medium", 26)
    texto = config.USUARIO_IG
    w = draw.textlength(texto, font=f)
    draw.text(((ANCHO - w) / 2, ALTO - 70), texto, font=f, fill=(190, 198, 220))


# ---------- Iconos simples dibujados ----------
def _icono_ubicacion(d, x, y, c):
    d.ellipse((x, y, x + 30, y + 30), fill=c)
    d.polygon([(x + 3, y + 21), (x + 27, y + 21), (x + 15, y + 42)], fill=c)
    d.ellipse((x + 9, y + 9, x + 21, y + 21), fill=config.COLOR_TARJETA)


def _icono_empresa(d, x, y, c):
    d.rectangle((x + 2, y + 6, x + 28, y + 40), fill=c)
    for fy in (12, 22, 32):
        for fx in (7, 17):
            d.rectangle((x + fx, y + fy, x + fx + 6, y + fy + 5), fill=config.COLOR_TARJETA)


def _icono_calendario(d, x, y, c):
    d.rounded_rectangle((x, y + 6, x + 32, y + 40), radius=5, fill=c)
    d.rectangle((x + 4, y + 16, x + 28, y + 36), fill=config.COLOR_TARJETA)
    d.rectangle((x + 7, y, x + 11, y + 10), fill=c)
    d.rectangle((x + 21, y, x + 25, y + 10), fill=c)


def portada(ofertas: list[dict], dia: date, ruta: Path) -> Path:
    img = Image.new("RGBA", (ANCHO, ALTO), config.COLOR_FONDO + (255,))
    _decoracion(img)
    d = ImageDraw.Draw(img)
    _cabecera(d)

    d.text((80, 240), "OFERTAS", font=_fuente("ExtraBold", 120), fill=config.COLOR_TEXTO)
    d.text((80, 370), "DE EMPLEO", font=_fuente("ExtraBold", 120), fill=config.COLOR_TEXTO)
    d.text((80, 500), "SANITARIO", font=_fuente("ExtraBold", 120), fill=config.COLOR_ACENTO)
    d.text((84, 660), fecha_larga(dia).capitalize(), font=_fuente("SemiBold", 40), fill=(200, 208, 230))

    # Resumen de categorías
    conteo: dict[str, int] = {}
    for o in ofertas:
        conteo[categoria(o["titulo"])] = conteo.get(categoria(o["titulo"]), 0) + 1
    y = 780
    fp = _fuente("Bold", 30)
    x = 80
    for nombre, n in sorted(conteo.items(), key=lambda kv: -kv[1]):
        etiqueta = f"{nombre}  {n}"
        w = d.textlength(etiqueta, font=fp) + 50
        if x + w > ANCHO - 80:
            x, y = 80, y + 80
        d.rounded_rectangle((x, y, x + w, y + 60), radius=30, outline=config.COLOR_TEXTO, width=3)
        d.text((x + 25, y + 13), etiqueta, font=fp, fill=config.COLOR_TEXTO)
        x += w + 16

    # Botón desliza
    n = len(ofertas)
    texto = f"{n} oferta{'s' if n != 1 else ''} nueva{'s' if n != 1 else ''}  ·  Desliza  →"
    fb = _fuente("ExtraBold", 38)
    w = d.textlength(texto, font=fb)
    d.rounded_rectangle((80, 1110, 80 + w + 80, 1200), radius=45, fill=config.COLOR_ACENTO)
    d.text((120, 1133), texto, font=fb, fill=config.COLOR_TEXTO)
    _pie(d)

    img.convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def ficha_oferta(o: dict, indice: int, total: int, ruta: Path) -> Path:
    img = Image.new("RGBA", (ANCHO, ALTO), config.COLOR_FONDO + (255,))
    _decoracion(img)
    d = ImageDraw.Draw(img)
    _cabecera(d, f"{indice}/{total}")

    # Etiqueta de categoría
    cat = categoria(o["titulo"])
    fc = _fuente("Bold", 30)
    w = d.textlength(cat, font=fc)
    d.rounded_rectangle((80, 200, 80 + w + 56, 262), radius=31, fill=config.COLOR_ACENTO)
    d.text((108, 214), cat, font=fc, fill=config.COLOR_TEXTO)

    # Tarjeta blanca
    x0, y0, x1, y1 = 60, 300, ANCHO - 60, 1150
    d.rounded_rectangle((x0, y0, x1, y1), radius=40, fill=config.COLOR_TARJETA)
    px = x0 + 60
    ancho_util = (x1 - 60) - px

    d.text((px, y0 + 55), "SE BUSCA", font=_fuente("Bold", 30), fill=config.COLOR_ACENTO)
    puesto, detalle = separar_titulo(o["titulo"])
    f, lineas, inter = _ajustar_titulo(d, puesto, ancho_util, alto_max=330 if detalle else 440)
    y = y0 + 110
    for linea in lineas:
        d.text((px, y), linea, font=f, fill=config.COLOR_TEXTO_TARJETA)
        y += inter
    if detalle:
        fdet = _fuente("SemiBold", 36)
        y += 12
        for linea in _envolver(d, detalle, fdet, ancho_util)[:3]:
            d.text((px, y), linea, font=fdet, fill=config.COLOR_SECUNDARIO)
            y += 46

    # Datos
    y = max(y + 30, y1 - 330)
    d.line((px, y, x1 - 60, y), fill=(225, 229, 238), width=3)
    y += 40
    fd = _fuente("SemiBold", 36)
    lugar = o["localidad"]
    if o["provincia"] and o["provincia"].lower() not in lugar.lower():
        lugar = f"{lugar}, {o['provincia']}" if lugar else o["provincia"]
    try:
        publicada = datetime.fromisoformat(o["fecha"]).strftime("%d/%m/%Y")
    except ValueError:
        publicada = "—"
    filas = [
        (_icono_ubicacion, lugar or "Ver oferta"),
        (_icono_empresa, o["empresa"]),
        (_icono_calendario, f"Publicada el {publicada}"),
    ]
    for icono, texto in filas:
        icono(d, px, y, config.COLOR_ACENTO)
        texto = _envolver(d, texto, fd, ancho_util - 70)[0]
        d.text((px + 60, y + 2), texto, font=fd, fill=config.COLOR_TEXTO_TARJETA)
        y += 78

    # Referencia dentro de la tarjeta (abajo a la derecha)
    fr = _fuente("SemiBold", 28)
    ref = f"Ref. {o['id']}"
    d.text((x1 - 60 - d.textlength(ref, font=fr), y1 - 55), ref, font=fr, fill=config.COLOR_SECUNDARIO)

    # Llamada a la acción: portal oficial, centrada
    fb = _fuente("ExtraBold", 34)
    cta = "Inscríbete en empleo.quironsalud.es"
    w = d.textlength(cta, font=fb)
    x = (ANCHO - w - 70) / 2
    d.rounded_rectangle((x, 1180, x + w + 70, 1260), radius=40, fill=config.COLOR_ACENTO)
    d.text((x + 35, 1201), cta, font=fb, fill=config.COLOR_TEXTO)

    img.convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def generar_carrusel(ofertas: list[dict], dia: date, carpeta: Path) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = [portada(ofertas, dia, carpeta / "00_portada.jpg")]
    for i, o in enumerate(ofertas, start=1):
        rutas.append(ficha_oferta(o, i, len(ofertas), carpeta / f"{i:02d}_{o['id']}.jpg"))
    return rutas


# ============ HISTORIAS (1080x1920, formato 9:16 vertical, optimizado para móvil) ============
ALTO_H = 1920
# Zonas seguras: Instagram superpone su interfaz arriba (~230 px: foto y usuario) y
# abajo (~250 px: barra de respuesta). Todo el contenido clave va entre esas franjas.


def _decoracion_h(img):
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    r, g, b = config.COLOR_ACENTO
    W, H = img.size
    d.ellipse((W - 360, -320, W + 280, 380), fill=(r, g, b, 60))
    d.ellipse((-260, H - 380, 240, H + 220), fill=(255, 255, 255, 16))
    img.alpha_composite(capa)


def _cabecera_h(d, derecha: str = ""):
    d.text((80, 250), config.NOMBRE_CUENTA.upper(), font=_fuente("Bold", 34), fill=config.COLOR_TEXTO)
    d.rectangle((80, 306, 158, 313), fill=config.COLOR_ACENTO)
    if derecha:
        fd = _fuente("SemiBold", 32)
        d.text((ANCHO - 80 - d.textlength(derecha, font=fd), 252), derecha, font=fd, fill=config.COLOR_TEXTO)


def _cta_bio_h(d, principal: str):
    """Banda inferior común: botón del portal oficial + aviso del enlace de la bio."""
    fb = _fuente("ExtraBold", 42)
    while d.textlength(principal, font=fb) > ANCHO - 150 and fb.size > 28:
        fb = _fuente("ExtraBold", fb.size - 2)
    w = d.textlength(principal, font=fb)
    x = (ANCHO - w - 80) / 2
    d.rounded_rectangle((x, 1540, x + w + 80, 1636), radius=48, fill=config.COLOR_ACENTO)
    d.text((x + 40, 1562), principal, font=fb, fill=config.COLOR_TEXTO)
    aviso = "Enlace directo en la bio"
    fa = _fuente("SemiBold", 34)
    d.text(((ANCHO - d.textlength(aviso, font=fa)) / 2, 1676), aviso, font=fa, fill=(205, 212, 232))
    fu = _fuente("Medium", 30)
    d.text(((ANCHO - d.textlength(config.USUARIO_IG, font=fu)) / 2, 1800),
           config.USUARIO_IG, font=fu, fill=(150, 162, 190))


def portada_historia(ofertas: list[dict], dia: date, ruta: Path) -> Path:
    img = Image.new("RGBA", (ANCHO, ALTO_H), config.COLOR_FONDO + (255,))
    _decoracion_h(img)
    d = ImageDraw.Draw(img)
    _cabecera_h(d)

    d.text((80, 470), "OFERTAS", font=_fuente("ExtraBold", 132), fill=config.COLOR_TEXTO)
    d.text((80, 616), "DE EMPLEO", font=_fuente("ExtraBold", 132), fill=config.COLOR_TEXTO)
    d.text((80, 762), "SANITARIO", font=_fuente("ExtraBold", 132), fill=config.COLOR_ACENTO)
    n = len(ofertas)
    sub = f"{fecha_larga(dia).capitalize()}  ·  {n} oferta{'s' if n != 1 else ''} en Madrid"
    fs = _fuente("SemiBold", 42)
    while d.textlength(sub, font=fs) > ANCHO - 168 and fs.size > 30:
        fs = _fuente("SemiBold", fs.size - 2)
    d.text((84, 946), sub, font=fs, fill=(200, 208, 230))

    # Resumen de categorías
    conteo: dict[str, int] = {}
    for o in ofertas:
        conteo[categoria(o["titulo"])] = conteo.get(categoria(o["titulo"]), 0) + 1
    y, x = 1090, 80
    fp = _fuente("Bold", 32)
    for nombre, cnt in sorted(conteo.items(), key=lambda kv: -kv[1]):
        etiqueta = f"{nombre}  {cnt}"
        w = d.textlength(etiqueta, font=fp) + 54
        if x + w > ANCHO - 80:
            x, y = 80, y + 86
        d.rounded_rectangle((x, y, x + w, y + 66), radius=33, outline=config.COLOR_TEXTO, width=3)
        d.text((x + 27, y + 15), etiqueta, font=fp, fill=config.COLOR_TEXTO)
        x += w + 16

    _cta_bio_h(d, "empleo.quironsalud.es")
    img.convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def ficha_historia(o: dict, indice: int, total: int, ruta: Path) -> Path:
    img = Image.new("RGBA", (ANCHO, ALTO_H), config.COLOR_FONDO + (255,))
    _decoracion_h(img)
    d = ImageDraw.Draw(img)
    _cabecera_h(d, f"{indice}/{total}")

    cat = categoria(o["titulo"])
    fc = _fuente("Bold", 32)
    w = d.textlength(cat, font=fc)
    d.rounded_rectangle((80, 384, 80 + w + 60, 452), radius=34, fill=config.COLOR_ACENTO)
    d.text((110, 399), cat, font=fc, fill=config.COLOR_TEXTO)

    x0, y0, x1, y1 = 60, 496, ANCHO - 60, 1470
    d.rounded_rectangle((x0, y0, x1, y1), radius=44, fill=config.COLOR_TARJETA)
    px = x0 + 60
    ancho_util = (x1 - 60) - px

    d.text((px, y0 + 56), "SE BUSCA", font=_fuente("Bold", 32), fill=config.COLOR_ACENTO)
    puesto, detalle = separar_titulo(o["titulo"])
    f, lineas, inter = _ajustar_titulo(d, puesto, ancho_util, alto_max=380 if detalle else 520)
    y = y0 + 120
    for linea in lineas:
        d.text((px, y), linea, font=f, fill=config.COLOR_TEXTO_TARJETA)
        y += inter
    if detalle:
        fdet = _fuente("SemiBold", 38)
        y += 14
        for linea in _envolver(d, detalle, fdet, ancho_util)[:3]:
            d.text((px, y), linea, font=fdet, fill=config.COLOR_SECUNDARIO)
            y += 50

    y = max(y + 40, y1 - 350)
    d.line((px, y, x1 - 60, y), fill=(225, 229, 238), width=3)
    y += 44
    fdd = _fuente("SemiBold", 38)
    lugar = o["localidad"]
    if o["provincia"] and o["provincia"].lower() not in lugar.lower():
        lugar = f"{lugar}, {o['provincia']}" if lugar else o["provincia"]
    try:
        publicada = datetime.fromisoformat(o["fecha"]).strftime("%d/%m/%Y")
    except ValueError:
        publicada = "—"
    for icono, texto in [(_icono_ubicacion, lugar or "Ver oferta"),
                         (_icono_empresa, o["empresa"]),
                         (_icono_calendario, f"Publicada el {publicada}")]:
        icono(d, px, y, config.COLOR_ACENTO)
        texto = _envolver(d, texto, fdd, ancho_util - 70)[0]
        d.text((px + 60, y + 2), texto, font=fdd, fill=config.COLOR_TEXTO_TARJETA)
        y += 82

    fr = _fuente("SemiBold", 30)
    ref = f"Ref. {o['id']}"
    d.text((x1 - 60 - d.textlength(ref, font=fr), y1 - 58), ref, font=fr, fill=config.COLOR_SECUNDARIO)

    _cta_bio_h(d, "Inscríbete en empleo.quironsalud.es")
    img.convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def generar_historias(ofertas: list[dict], dia: date, carpeta: Path) -> list[Path]:
    """Genera las imágenes verticales (9:16) para publicar como Historias."""
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = [portada_historia(ofertas, dia, carpeta / "h00_portada.jpg")]
    for i, o in enumerate(ofertas, start=1):
        rutas.append(ficha_historia(o, i, len(ofertas), carpeta / f"h{i:02d}_{o['id']}.jpg"))
    return rutas
