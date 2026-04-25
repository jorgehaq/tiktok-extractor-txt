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
streamlit run app.py
```

## Arquitectura de la Planta 🏗️

- **`init_db()`**: Forja la base de datos `tiktok_knowledge.db` si no existe. Crea los compartimentos exactos para la contención (`id`, `url`, `title`, `author`, `description`, `tags`, `transcript`, `main_category`, `keywords`).
- **`get_full_metadata()`**: Utiliza el comando `yt-dlp --dump-json` para hacer una radiografía profunda al video y sacar la data estructural, operando rápido sin descargar el archivo pesado.
- **`get_audio_and_transcribe()`**: Extrae la pista en mp3 usando un archivo temporal y la pasa por el modelo `base` de Whisper (ejecutado en CPU) para generar la transcripción. 

## Reglas de Mantenimiento y Rendimiento 🛑
- **`.gitignore`**: Ya está configurado como tu escudo, ignorando el subconsciente temporal de Python (`__pycache__`, `*.py[cod]`, entornos virtuales y descargas), evitando fugar basura a tu "Alcalde" en la nube (GitHub).
- **Caché del Modelo**: El script utiliza el decorador `@st.cache_resource` sobre la función `load_whisper()`. Esto es vital: asegura que el modelo masivo de inteligencia artificial se cargue una sola vez en la memoria RAM. Evita que la aplicación colapse (un *shutdown* del sistema) al recalcular en cada clic de la interfaz.