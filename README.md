# TikTok Extractor TXT ☢️

## El Mapa (La Analogía del Sistema)
Este proyecto no es un simple *scraper*, es una **Planta de Enriquecimiento de Uranio para el Conocimiento**. 
Internet y las redes sociales son minas caóticas llenas de ruido. Este sistema actúa como la centrífuga que aísla la información útil para que tu cerebro (AACC/TEA) pueda procesarla sin hiperestimularse visualmente:

- **yt-dlp (El Brazo Robótico):** Extrae el bloque completo de datos crudos de la mina.
- **Whisper (El Decodificador Cuántico):** Filtra el ruido y extrae el isótopo puro (la transcripción exacta del audio en texto).
- **SQLite (La Vasija de Contención):** Almacena de forma ordenada y blindada (tu "diario de bolsillo") cada átomo de información extraído.
- **Streamlit (El Panel de Control):** La interfaz limpia y sin fricciones para operar el reactor sin distracciones.

## Stack Tecnológico 🛠️
- **Frontend/UI:** Streamlit
- **Base de Datos:** SQLite nativo (`tiktok_knowledge.db`)
- **Core de Extracción:** `yt-dlp`, módulo `subprocess`
- **Motor de IA/Audio:** `whisper` (OpenAI)
- **Gestión de Entorno:** `uv` (Rápido, pragmático, sin rodeos)

## Protocolo de Arranque (Ejecución) ⚙️

### 1. Activar el Búnker (Entorno Virtual con `uv`)
Debes aislar la radiación de este proyecto del resto de tu sistema operativo.
```bash
# Crear el entorno virtual con uv
uv venv

# Activar el entorno (WSL / Linux / macOS)
source .venv/bin/activate
```

### 2. Inyectar el Refrigerante (Dependencias)
Dado que el archivo `requirements.txt` está vacío en el repositorio actual, estas son las barras de control obligatorias que la aplicación necesita para hacer fisión según el código fuente.
```bash
uv pip install streamlit openai-whisper yt-dlp
```

*Nota técnica estructural:* Para que `yt-dlp` pueda extraer el formato mp3 y `whisper` pueda procesarlo, el sistema operativo base requiere el motor multimedia. Si estás en Ubuntu/WSL, asegúrate de tenerlo instalado:
```bash
sudo apt update && sudo apt install ffmpeg
```

### 3. Ignición del Reactor (Lanzamiento)
Una vez que el entorno está aislado y cargado, levanta el panel de control:
```bash
streamlit run app.py --server.headless true
```

## Arquitectura de la Planta 🏗️

- **`init_db()`**: Forja la base de datos `tiktok_knowledge.db` si no existe. Crea los compartimentos exactos para la contención (`id`, `url`, `title`, `author`, `description`, `tags`, `transcript`, `main_category`, `keywords`).
- **`get_full_metadata()`**: Utiliza el comando `yt-dlp --dump-json` para hacer una radiografía profunda al video y sacar la data estructural, operando rápido sin descargar el archivo pesado.
- **`get_audio_and_transcribe()`**: Extrae la pista en mp3 usando un archivo temporal y la pasa por el modelo `base` de Whisper (ejecutado en CPU) para generar la transcripción. 

## Reglas de Mantenimiento y Rendimiento 🛑
- **`.gitignore`**: Ya está configurado como tu escudo, ignorando el subconsciente temporal de Python (`__pycache__`, `*.py[cod]`, entornos virtuales y descargas), evitando fugar basura a tu "Alcalde" en la nube (GitHub).
- **Caché del Modelo**: El script utiliza el decorador `@st.cache_resource` sobre la función `load_whisper()`. Esto es vital: asegura que el modelo masivo de inteligencia artificial se cargue una sola vez en la memoria RAM. Evita que la aplicación colapse (un *shutdown* del sistema) al recalcular en cada clic de la interfaz.

## El Muro de Contención (Diagnóstico del Error 403 Forbidden)

Te has topado con el **Cadenero del Club Nocturno**. TikTok detectó que el video tiene restricciones de contenido (audiencias sensibles) o ha notado un comportamiento de extracción, levantando un muro y exigiendo ver una identificación. 

Tu brazo robótico (`yt-dlp`) está intentando entrar al club con la cara en blanco, como un usuario anónimo. Para solucionarlo, no necesitas crearle una cuenta al robot, sino prestarle tu **Pase VIP** (las *Cookies* de tu navegador) y ponerle una **Máscara Biométrica** (Impersonation).

### La Solución: Inyectar el Pase VIP y la Máscara (`--cookies` + `--impersonate`)

**1. Autenticación Orgánica en la Base**
Abre tu navegador principal, entra a `tiktok.com` y asegúrate de tener una sesión activa con tu cuenta humana. Exporta estas cookies a un archivo `cookies.txt` en la raíz de tu proyecto.

**2. Inyectar librerías de suplantación avanzada (Impersonation targets)**
Para que la máscara funcione, necesitas instalar un par de dependencias que le permiten a `yt-dlp` imitar las huellas digitales de un navegador real:
```bash
uv pip install curl-cffi requests
uv pip install --upgrade yt-dlp
```

**3. Activar la Máscara en el Código (`app.py`)**
Debes ordenarle explícitamente a `yt-dlp` que utilice esta nueva capacidad biométrica al hacer la petición. Añade el parámetro `--impersonate` a tus listas de comandos junto con tus cookies (`--cookies cookies.txt`).

```python
# EJEMPLO DE IMPLEMENTACIÓN

# 1. En la extracción de Metadatos (get_full_metadata):
command_meta = [
    "python", "-m", "yt_dlp",        # <--- ENRUTAMIENTO FORZADO AL BÚNKER
    "--cookies", "cookies.txt",
    # EL ESPEJO: La huella digital exacta de Windows/Chrome
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "--no-playlist", "--dump-json", "--quiet",
    "-o", os.path.join(tmp_dir, "%(id)s.%(ext)s"), 
    url
]

# 2. En la extracción de Audio (get_audio_and_transcribe):
command_audio = [
    "python", "-m", "yt_dlp",        # <--- ENRUTAMIENTO FORZADO AL BÚNKER
    "--cookies", "cookies.txt",
    # EL ESPEJO: La huella digital exacta de Windows/Chrome
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "-x", "--audio-format", "mp3",
    "--audio-quality", "0",
    "-o", os.path.join(tmp_dir, "temp_audio.%(ext)s"),
    url
]
```

### Protocolo de Mantenimiento Continuo
En la minería de datos de redes sociales, esta es una guerra armamentista. Si en un par de semanas vuelve a aparecer un `403 Forbidden`, la regla de oro es que la máscara se desactualizó. Simplemente corres un `uv pip install --upgrade yt-dlp` y el robot volverá a entrar al club. Vuelve a arrancar tu servidor con `--server.headless true` y prueba la extracción.

### Notas de Contingencia ⚠️

- **El Bloqueo del Archivo (Windows):** Si al usar la opción antigua de `--cookies-from-browser` te arroja un error de que la base de datos está bloqueada (`database is locked`), es porque tu navegador tiene el archivo de cookies secuestrado en memoria. Cierra tu navegador para liberar el archivo. Usar `cookies.txt` evita este problema por completo.
- **El Warning de 'Impersonation':** El mensaje amarillo sobre "impersonation" indica que `yt-dlp` está intentando ponerse su máscara avanzada. Gracias a la instalación de `curl-cffi`, este proceso ahora tiene las dependencias correctas para funcionar sin arrojar errores.