"""
CONFIGURACIÓN — edita solo este archivo para personalizar la cuenta.
"""

# ---------- Marca de TU cuenta (no uses el logo ni el nombre de Quirónsalud como marca) ----------
NOMBRE_CUENTA = "Empleo Sanidad Madrid"     # Nombre que aparece en las creatividades
USUARIO_IG = "@ofertasempleosanidadmadrid"  # Tu @ de Instagram
HASHTAGS = [
    # Alto volumen (alcance)
    "#empleo", "#trabajo", "#ofertasdeempleo", "#ofertadeempleo", "#buscotrabajo",
    "#buscoempleo", "#bolsadeempleo", "#trabajoenespaña", "#madrid",
    # Madrid (audiencia local)
    "#empleomadrid", "#trabajomadrid", "#trabajoenmadrid", "#madridempleo",
    # Nicho sanitario (seguidores cualificados)
    "#sanidad", "#empleosanitario", "#enfermeria", "#enfermera", "#enfermero",
    "#tcae", "#auxiliardeenfermeria", "#medicina", "#medico", "#fisioterapia",
    "#farmacia", "#oposicionessanidad", "#hospital", "#salud", "#celador",
    "#quirofano", "#urgencias",
]

# ---------- Colores (RGB) ----------
COLOR_FONDO = (15, 27, 61)        # azul noche
COLOR_ACENTO = (255, 107, 91)     # coral
COLOR_TEXTO = (255, 255, 255)
COLOR_TARJETA = (255, 255, 255)
COLOR_TEXTO_TARJETA = (15, 27, 61)
COLOR_SECUNDARIO = (110, 120, 150)

# ---------- Fuente de ofertas ----------
URL_LISTADO = (
    "https://empleo-grupoquironsalud.talentclue.com/es/company/"
    "102ba0383b7d45e10c9679e94613c9a9/jsoffers/modal?op=1&sort=desc&order=Fecha"
)
URL_BASE_OFERTA = "https://empleo-grupoquironsalud.talentclue.com/es/node/{id}/4590"

# ---------- Publicación ----------
MAX_OFERTAS_POR_DIA = 9           # Carrusel: portada + hasta 9 ofertas (máx. 10 imágenes)
MIN_OFERTAS_PARA_PUBLICAR = 1     # Si hay menos ofertas nuevas, no se publica ese día

# Filtrar por provincia/localidad (vacío = toda España). Ej: ["Madrid"]
FILTRO_ZONAS: list[str] = ["Madrid"]

# Días que se guardan las imágenes generadas en el repositorio
DIAS_CONSERVAR_IMAGENES = 7
