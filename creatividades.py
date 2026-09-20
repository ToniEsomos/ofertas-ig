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
    texto = f"{config.USUARIO_IG}  ·  Cuenta no oficial"
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

    # Llamada a la acción
    fb = _fuente("ExtraBold", 36)
    cta = "Inscríbete: enlace en la bio"
    w = d.textlength(cta, font=fb)
    d.rounded_rectangle((80, 1180, 80 + w + 70, 1260), radius=40, fill=config.COLOR_ACENTO)
    d.text((115, 1199), cta, font=fb, fill=config.COLOR_TEXTO)
    fr = _fuente("SemiBold", 28)
    ref = f"Ref. {o['id']}"
    d.text((ANCHO - 80 - d.textlength(ref, font=fr), 1205), ref, font=fr, fill=(200, 208, 230))

    img.convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def generar_carrusel(ofertas: list[dict], dia: date, carpeta: Path) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = [portada(ofertas, dia, carpeta / "00_portada.jpg")]
    for i, o in enumerate(ofertas, start=1):
        rutas.append(ficha_oferta(o, i, len(ofertas), carpeta / f"{i:02d}_{o['id']}.jpg"))
    return rutas
