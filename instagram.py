"""
Publica un carrusel en Instagram con la API oficial (Instagram API with Instagram Login).

Variables de entorno necesarias:
  IG_USER_ID       -> ID de tu cuenta profesional de Instagram
  IG_ACCESS_TOKEN  -> token de larga duración (dura 60 días; ver README para renovarlo)
Opcional:
  IG_API_VERSION   -> por defecto v23.0
"""
import os
import time

import requests

API = "https://graph.instagram.com/{version}"


class ErrorInstagram(Exception):
    pass


def _cfg():
    user_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not user_id or not token:
        raise ErrorInstagram("Faltan IG_USER_ID o IG_ACCESS_TOKEN.")
    base = API.format(version=os.environ.get("IG_API_VERSION", "v23.0"))
    return base, user_id, token


def _post(url, datos):
    r = requests.post(url, data=datos, timeout=60)
    js = r.json()
    if r.status_code != 200 or "error" in js:
        raise ErrorInstagram(f"{url} -> {js}")
    return js


def _esperar_contenedor(base, token, id_contenedor, max_espera=180):
    t0 = time.time()
    while time.time() - t0 < max_espera:
        r = requests.get(f"{base}/{id_contenedor}",
                         params={"fields": "status_code", "access_token": token}, timeout=30)
        estado = r.json().get("status_code")
        if estado == "FINISHED":
            return
        if estado in ("ERROR", "EXPIRED"):
            raise ErrorInstagram(f"Contenedor {id_contenedor} en estado {estado}: {r.json()}")
        time.sleep(5)
    raise ErrorInstagram(f"Tiempo de espera agotado para {id_contenedor}")


def publicar_carrusel(urls_imagenes: list[str], texto: str) -> str:
    """Sube de 2 a 10 imágenes (URLs públicas JPEG) como carrusel. Devuelve el ID del post."""
    if not 2 <= len(urls_imagenes) <= 10:
        raise ErrorInstagram("Un carrusel necesita entre 2 y 10 imágenes.")
    base, user_id, token = _cfg()

    hijos = []
    for url in urls_imagenes:
        js = _post(f"{base}/{user_id}/media",
                   {"image_url": url, "is_carousel_item": "true", "access_token": token})
        hijos.append(js["id"])
    for h in hijos:
        _esperar_contenedor(base, token, h)

    carrusel = _post(f"{base}/{user_id}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(hijos),
        "caption": texto,
        "access_token": token,
    })["id"]
    _esperar_contenedor(base, token, carrusel)

    publicado = _post(f"{base}/{user_id}/media_publish",
                      {"creation_id": carrusel, "access_token": token})
    return publicado["id"]


def publicar_imagen(url_imagen: str, texto: str) -> str:
    """Publica UNA imagen (URL pública JPEG) como publicación de feed. Devuelve el ID."""
    base, user_id, token = _cfg()
    cont = _post(f"{base}/{user_id}/media",
                 {"image_url": url_imagen, "caption": texto, "access_token": token})["id"]
    _esperar_contenedor(base, token, cont)
    ultimo = None
    for _ in range(8):
        try:
            return _post(f"{base}/{user_id}/media_publish",
                         {"creation_id": cont, "access_token": token})["id"]
        except ErrorInstagram as e:
            ultimo = e
            if "2207027" in str(e) or "9007" in str(e) or "not ready" in str(e).lower():
                time.sleep(8)
                continue
            raise
    raise ultimo


def publicar_historia(url_imagen: str) -> str:
    """Publica UNA imagen (URL pública JPEG) como Historia. Devuelve el ID.

    Nota: la API de Instagram NO permite añadir stickers de enlace ni otros
    elementos interactivos a las historias; solo la imagen.
    """
    base, user_id, token = _cfg()
    cont = _post(f"{base}/{user_id}/media",
                 {"image_url": url_imagen, "media_type": "STORIES", "access_token": token})["id"]
    _esperar_contenedor(base, token, cont)
    # A veces el contenedor da FINISHED pero aún no está listo para publicar (código 9007).
    ultimo = None
    for _ in range(8):
        try:
            return _post(f"{base}/{user_id}/media_publish",
                         {"creation_id": cont, "access_token": token})["id"]
        except ErrorInstagram as e:
            ultimo = e
            if "2207027" in str(e) or "9007" in str(e) or "not ready" in str(e).lower():
                time.sleep(8)
                continue
            raise
    raise ultimo


def publicar_historias(urls_imagenes: list[str]) -> list[str]:
    """Publica varias imágenes como historias, cada una en su propio frame."""
    ids = []
    for url in urls_imagenes:
        ids.append(publicar_historia(url))
    return ids


def renovar_token(token_actual: str) -> dict:
    """Renueva un token de larga duración (debe tener >24 h y no estar caducado)."""
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": token_actual},
                     timeout=30)
    return r.json()
