"""
Lee el listado de ofertas del portal de empleo (Talent Clue) y devuelve una lista de dicts.
"""
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}
MAX_PAGINAS = 10


def _limpiar(texto: str) -> str:
    texto = (texto or "").replace("_", " ").replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto).strip(" ·-–")
    return texto


def _titulo_bonito(titulo: str) -> str:
    titulo = _limpiar(titulo).replace("@", "o/a")
    titulo = re.sub(r"\s*/\s*", "/", titulo)  # "Celador / a" -> "Celador/a"
    if titulo.isupper():  # "ENFERMERO/A QUIRÓFANO" -> "Enfermero/a quirófano"
        titulo = titulo.lower()
        titulo = titulo[0].upper() + titulo[1:]
    return titulo


def _lugar_bonito(texto: str) -> str:
    texto = _limpiar(texto)
    if texto in ("", "-"):
        return ""
    if texto.isupper() or texto.islower():
        texto = " ".join(p.capitalize() if len(p) > 2 else p.lower() for p in texto.lower().split())
        texto = texto[0].upper() + texto[1:]
    return texto


def _parsear_pagina(html: str, url_pagina: str) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    ofertas = []
    for fila in soup.find_all("tr"):
        celdas = fila.find_all("td")
        if len(celdas) < 6:
            continue
        enlace = celdas[1].find("a", href=True)
        if not enlace:
            continue
        m = re.search(r"/node/(\d+)", enlace["href"])
        if not m:
            continue
        id_oferta = m.group(1)
        fecha_txt = _limpiar(celdas[5].get_text())
        try:
            fecha = datetime.strptime(fecha_txt, "%d/%m/%Y").date().isoformat()
        except ValueError:
            fecha = ""
        ofertas.append({
            "id": id_oferta,
            "titulo": _titulo_bonito(enlace.get_text()),
            "empresa": _limpiar(celdas[2].get_text()) or "Quirónsalud",
            "localidad": _lugar_bonito(celdas[3].get_text()),
            "provincia": _lugar_bonito(celdas[4].get_text()),
            "fecha": fecha,
            "url": config.URL_BASE_OFERTA.format(id=id_oferta),
        })

    # Paginación (si existe)
    siguiente = soup.select_one("li.pager-next a[href], a[rel=next][href], a[title*='siguiente' i][href]")
    url_siguiente = urljoin(url_pagina, siguiente["href"]) if siguiente else None
    return ofertas, url_siguiente


def obtener_ofertas() -> list[dict]:
    """Devuelve todas las ofertas activas, de más nueva a más antigua, sin duplicados."""
    url = config.URL_LISTADO
    vistas, resultado = set(), []
    for _ in range(MAX_PAGINAS):
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        ofertas, url_siguiente = _parsear_pagina(r.text, url)
        for o in ofertas:
            if o["id"] not in vistas:
                vistas.add(o["id"])
                resultado.append(o)
        if not url_siguiente or url_siguiente == url:
            break
        url = url_siguiente
        time.sleep(2)  # ser respetuoso con el servidor

    resultado.sort(key=lambda o: o["fecha"], reverse=True)
    return resultado


def filtrar_por_zona(ofertas: list[dict]) -> list[dict]:
    if not config.FILTRO_ZONAS:
        return ofertas
    zonas = [z.lower() for z in config.FILTRO_ZONAS]
    return [
        o for o in ofertas
        if any(z in f"{o['localidad']} {o['provincia']} {o['titulo']}".lower() for z in zonas)
    ]


if __name__ == "__main__":
    for o in obtener_ofertas()[:15]:
        print(o["fecha"], "|", o["titulo"], "|", o["localidad"], o["provincia"])
