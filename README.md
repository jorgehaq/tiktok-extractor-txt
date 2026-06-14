# TikTok Extractor TXT 🧠

Sistema simplificado de extracción, transcripción y clasificación inteligente para videos de TikTok. Diseñado para aislar la información útil en texto limpio, eliminando la hiperestimulación visual y el ruido de las redes sociales.

## Stack Tecnológico 🛠️
- **Frontend/UI:** Streamlit
- **Base de Datos:** SQLite nativo (`tiktok_knowledge.db`)
- **Core de Extracción:** `yt-dlp` ejecutado de forma nativa
- **Motor de Audio:** `whisper` (OpenAI, ejecutado localmente en CPU)
- **Gestión de Entorno:** `uv` (Sin activaciones manuales de entornos virtuales)
- **Cerebro AI:** `DeepSeek-V4-Flash` (Vía API directa)

---

## ⚙️ Protocolo de Arranque Rápido (Con `uv`)

Olvídate de crear, activar o gestionar carpetas `.venv`. El gestor `uv` se encarga de aislar y correr todo en su caché global de forma automática.

### 1. Inicializar el Entorno (Solo la primera vez)
Si clonaste el repositorio limpio o borraste la carpeta `.venv` antigua, prepara el proyecto ejecutando:
```bash
# Inicializa el espacio de configuración si no existe un pyproject.toml
uv init

# Inyecta las dependencias del núcleo de forma automática
uv add streamlit yt-dlp openai-whisper requests
```

> **Nota para Linux / WSL / macOS:** Para que el sistema pueda extraer y procesar las pistas multimedia (mp3), necesitas tener instalado `ffmpeg` en tu sistema operativo base:
> ```bash
> sudo apt update && sudo apt install ffmpeg
> ```

### 2. Configurar las Credenciales

Para el cerebro de clasificación y el acceso a los videos, necesitas dos llaves en la raíz del proyecto:

1. **La API Key de DeepSeek (`.env`):** Crea un archivo llamado `.env` en la raíz del proyecto y define tu variable de la siguiente manera:
```env
DEEPSEEK_API_KEY="tu_llave_privada_aquí"
```

2. **El Pase VIP de TikTok (`cookies.txt`):** Sigue las instrucciones de la sección de abajo para generar este archivo.

### 3. Ignición de la App

Lanza el panel de control directamente con un solo comando:

```bash
uv run streamlit run app.py --server.headless true
```

---

## 🍪 Guía: Cómo obtener tu `cookies.txt` para TikTok

TikTok utiliza bloqueos tipo *403 Forbidden* cuando detecta peticiones automatizadas anónimas. Al pasarle tus cookies de sesión activa, el script se comporta exactamente como tu navegador humano.

### Paso a Paso para generar el archivo:

1. **Instala una extensión de cookies en tu navegador:**
   * Para Chrome / Edge / Brave: Instala **"Get cookies.txt LOCALLY"** (asegúrate de que sea la versión local que respeta la privacidad).
   * Para Firefox: Instala **"Export Cookies.txt"**.

2. **Inicia sesión en TikTok:**
   * Abre una pestaña, entra a `tiktok.com` e inicia sesión con tu cuenta de forma normal. Navega un par de segundos.

3. **Exportar el archivo:**
   * Haz clic en el ícono de la extensión instalada mientras estás en la pestaña de TikTok.
   * Selecciona la opción para exportar o descargar las cookies en formato **Netscape** o **cookies.txt**.

4. **Ubicación en el proyecto:**
   * Toma el archivo descargado, renombralo exactamente a `cookies.txt` y colócalo en la **raíz** de este proyecto (junto a `app.py`).

> **Regla de Mantenimiento:** Las cookies expiran cada ciertas semanas. Si la aplicación vuelve a lanzar un error de denegación o restricción de edad, simplemente repite este proceso de exportación para renovar el archivo `cookies.txt`.