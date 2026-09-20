# Ofertas de empleo → Instagram (automático y gratis)

Cada día, este proyecto:

1. Lee las ofertas del portal de empleo de Quirónsalud (Talent Clue).
2. Detecta las nuevas y crea un carrusel (portada + hasta 9 fichas, 1080×1350).
3. Lo publica en tu Instagram con la API oficial de Meta.
4. Actualiza una web con todas las ofertas activas y su enlace de inscripción, para ponerla en tu bio.

Todo corre en **GitHub Actions** (gratis en repositorios públicos). Coste: 0 €.

---

## 1. Instagram (15 min)

1. Pasa tu cuenta a **profesional** (Configuración → Tipo de cuenta → Cuenta profesional: Empresa o Creador).
2. Entra en [developers.facebook.com](https://developers.facebook.com/) → **Crear app** → caso de uso **"Gestionar mensajes y contenido en Instagram"** (Instagram API con inicio de sesión de Instagram).
3. En **Configuración de la API con inicio de sesión de Instagram**, añade tu cuenta y pulsa **Generar token**. Acepta los permisos `instagram_business_basic` e `instagram_business_content_publish`.
4. Copia dos datos:
   - **Token de acceso** (larga duración, 60 días).
   - **ID de usuario de Instagram** (aparece junto a la cuenta).

> Como solo publicas en tu propia cuenta, la app puede quedarse en modo desarrollo; no necesitas pasar la revisión de Meta. Los nombres de los menús de Meta cambian a menudo: si no coinciden, busca "Instagram API with Instagram Login" en su documentación.

## 2. GitHub (10 min)

1. Crea una cuenta en [github.com](https://github.com) y un **repositorio público** (p. ej. `ofertas-ig`).
2. Sube todos los archivos de esta carpeta (botón *Add file → Upload files*, arrastrando la carpeta completa, incluida `.github`).
3. **Settings → Actions → General → Workflow permissions** → marca **Read and write permissions**.
4. **Settings → Secrets and variables → Actions → New repository secret**:
   - `IG_USER_ID` → tu ID de Instagram
   - `IG_ACCESS_TOKEN` → tu token
   - `GH_PAT` → *(opcional, para renovar el token solo)* un token personal de GitHub (Settings de tu perfil → Developer settings → Fine-grained tokens) con permiso **Secrets: Read and write** sobre este repositorio.
5. **Settings → Pages** → Source: *Deploy from a branch* → rama `main`, carpeta `/docs`. Te dará una URL tipo `https://tuusuario.github.io/ofertas-ig/` → **ponla en la bio de Instagram**.

## 3. Primera ejecución

En la pestaña **Actions → Publicar ofertas → Run workflow**:

- **Opción A (recomendada):** ejecuta primero `inicializar`. Marca las ofertas que ya existen como vistas y a partir de mañana solo se publican las nuevas.
- **Opción B:** ejecuta directamente `preparar-y-publicar`. Irá publicando las ofertas existentes (9 al día, de más nuevas a más antiguas), útil para arrancar la cuenta con contenido.

**Modo prueba:** si todavía no has puesto los secretos de Instagram, el flujo genera las imágenes en `output/AAAA-MM-DD/` y no publica nada. Ideal para revisar el diseño.

A partir de ahí se ejecuta solo cada día a las 09:00 (hora de Madrid en verano). Para cambiar la hora, edita `cron` en `.github/workflows/publicar.yml` (la hora va en UTC). GitHub puede retrasar unos minutos las tareas programadas.

## 4. Personalizar

Todo está en `config.py`:

| Qué | Variable |
|---|---|
| Nombre y @ de la cuenta | `NOMBRE_CUENTA`, `USUARIO_IG` |
| Colores | `COLOR_FONDO`, `COLOR_ACENTO`… |
| Hashtags | `HASHTAGS` |
| Ofertas por carrusel | `MAX_OFERTAS_POR_DIA` (máx. 9) |
| Solo ciertas zonas | `FILTRO_ZONAS = ["Madrid"]` |

Las categorías (Enfermería, TCAE, Medicina…) se detectan por palabras clave en `creatividades.py` → `CATEGORIAS`.

## 5. Mantenimiento

- **Token:** caduca a los 60 días. Con `GH_PAT` configurado se renueva solo (días 1 y 15). Sin él, genera uno nuevo en Meta y actualiza el secreto `IG_ACCESS_TOKEN`.
- **Si falla un día:** en *Actions* verás el error en rojo. Las ofertas no publicadas se intentan de nuevo al día siguiente.
- **Si el portal cambia de diseño**, habría que ajustar `scraper.py` (la tabla de ofertas).

## Estructura

```
config.py          Configuración
scraper.py         Lectura de ofertas
creatividades.py   Diseño de las imágenes
instagram.py       Publicación vía API
main.py            Orquestación (inicializar / preparar / publicar)
fonts/             Tipografía Montserrat (licencia OFL)
data/              Estado: ofertas vistas y pendientes
docs/              Web del enlace en bio (GitHub Pages)
output/            Imágenes generadas (se guardan 7 días)
```

## Uso responsable

- No uses el logotipo ni el nombre de Quirónsalud como marca de la cuenta; el proyecto ya indica "Cuenta no oficial" y remite siempre a la web oficial para inscribirse.
- Se hace una sola consulta al día al portal, con pausa entre páginas.
- Revisa las condiciones de uso del portal y, si la cuenta crece, plantéate pedirles permiso o una colaboración.
