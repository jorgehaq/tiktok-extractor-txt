import streamlit as st
import sqlite3
import json
import subprocess
import tempfile
import os
import whisper
import requests
import sys

# -- 0. AÑADIR FFMPEG LOCAL AL PATH --
local_bin = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin"))
if local_bin not in os.environ["PATH"]:
    os.environ["PATH"] = local_bin + os.pathsep + os.environ["PATH"]

# -- 0. CARGAR VARIABLES DE ENTORNO DESDE .ENV --
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

load_env()


# -- 1. CONFIGURACIÓN DE BASE DE DATOS Y MODELO AUDIO --

def init_db():
    with sqlite3.connect('tiktok_knowledge.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            author TEXT,
            description TEXT,
            tags TEXT,
            transcript TEXT,
            main_category TEXT,
            keywords TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

@st.cache_resource
def load_whisper():
    return whisper.load_model("base", device="cpu")

# -- 2. EXTRACCIÓN (yt-dlp + Whisper) --

def get_full_metadata(url, tmp_dir):
    use_cookies = os.path.exists("cookies.txt")
    cmd_base = [
        sys.executable, "-m", "yt_dlp",
        "--extractor-args", "tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com",
        "--no-playlist", "--dump-json", "--quiet",
        "-o", os.path.join(tmp_dir, "%(id)s.%(ext)s"), 
    ]
    
    if use_cookies:
        cmd = cmd_base + ["--cookies", "cookies.txt", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip().splitlines()[-1])
            except Exception:
                pass
                
    cmd = cmd_base + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout.strip().splitlines()[-1])
        except Exception:
            pass
            
    # Fallback: Usar TikWM API si yt-dlp falla por bloqueo de IP
    try:
        r = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get("code") == 0 and "data" in res:
                data = res["data"]
                title_desc = data.get("title", "")
                tags = [t.replace("#", "") for t in title_desc.split() if t.startswith("#")]
                return {
                    "title": title_desc,
                    "description": " ".join(data.get("content_desc", [])) if data.get("content_desc") else title_desc,
                    "uploader": data.get("author", {}).get("unique_id", "Autor Desconocido"),
                    "tags": tags,
                    "tikwm_audio_url": data.get("music"),
                }
    except Exception as e:
        print(f"Fallback TikWM failed: {e}", file=sys.stderr)
        
    return {}

def get_audio_and_transcribe(url, tmp_dir, model, tikwm_audio_url=None):
    if tikwm_audio_url:
        try:
            r = requests.get(tikwm_audio_url, timeout=20)
            if r.status_code == 200:
                audio_path = os.path.join(tmp_dir, "temp_audio.mp3")
                with open(audio_path, "wb") as f:
                    f.write(r.content)
                if os.path.exists(audio_path):
                    result = model.transcribe(audio_path, fp16=False)
                    return result.get("text", "").strip()
        except Exception as e:
            print(f"TikWM audio download failed: {e}", file=sys.stderr)

    use_cookies = os.path.exists("cookies.txt")
    cmd_base = [
        sys.executable, "-m", "yt_dlp",
        "--extractor-args", "tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com",
        "-f", "b[vcodec^=h264]/b[vcodec^=avc1]/b",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", os.path.join(tmp_dir, "temp_audio.%(ext)s"),
    ]
    
    success = False
    if use_cookies:
        cmd = cmd_base + ["--cookies", "cookies.txt", url]
        if subprocess.run(cmd).returncode == 0:
            success = True
            
    if not success:
        cmd = cmd_base + [url]
        if subprocess.run(cmd).returncode == 0:
            success = True
            
    audio_path = os.path.join(tmp_dir, "temp_audio.mp3")
    if os.path.exists(audio_path):
        result = model.transcribe(audio_path, fp16=False)
        return result.get("text", "").strip()
    return ""

# -- 3. PROCESAMIENTO CON DEEPSEEK IA --

def clasificar_con_ia(titulo, descripcion, transcripcion):
    prompt = f"""
    Analiza este contenido de TikTok y devuelve ÚNICAMENTE un objeto JSON válido.
    Título: {titulo}
    Descripción: {descripcion}
    Transcripción: {transcripcion}
    
    Estructura estricta del JSON de salida:
    {{
        "categoria_principal": "Elige una de: [Tecnología, Productividad, Tutoriales, Ocio, Finanzas, Otro]",
        "tipo_contenido": "Elige una de: [Tip/Truco, Reflexión, Noticia, Comedia, Review]",
        "palabras_clave": ["keyword1", "keyword2", "keyword3"]
    }}
    """
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return {
            "categoria_principal": "Otro",
            "tipo_contenido": "Noticia",
            "palabras_clave": ["error_falta_api_key"]
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        ai_response_text = data["choices"][0]["message"]["content"].strip()
        return json.loads(ai_response_text)
    except Exception:
        return {
            "categoria_principal": "Otro",
            "tipo_contenido": "Noticia",
            "palabras_clave": ["error_conexion_deepseek"]
        }

# -- 4. INTERFAZ DE USUARIO (Streamlit) --

st.set_page_config(page_title="TikTok Brain Extractor", layout="centered")
init_db()
whisper_model = load_whisper()

st.title("🧠 TikTok Knowledge Extractor")

# Inicializar estados de sesión para el botón de limpieza
if "url_value" not in st.session_state:
    st.session_state.url_value = ""
if "markdown_output" not in st.session_state:
    st.session_state.markdown_output = ""

def limpiar_interfaz():
    st.session_state.url_value = ""
    st.session_state.markdown_output = ""

# Control de entrada de la URL
url_input = st.text_input("🔗 Pega la URL del TikTok:", key="url_value")

col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    procesar_btn = st.button("🚀 Extraer y Clasificar", use_container_width=True)
with col_btn2:
    st.button("🧹 Limpiar", on_click=limpiar_interfaz, use_container_width=True)

if procesar_btn and url_input:
    with st.spinner("Centrifugando el isótopo de información..."):
        with tempfile.TemporaryDirectory() as tmp:
            
            meta = get_full_metadata(url_input, tmp)
            titulo = meta.get("title", "Sin Título")
            descripcion = meta.get("description", "Sin Descripción")
            autor = meta.get("uploader", "Autor Desconocido")
            tags_originales = ", ".join(meta.get("tags", [])) if meta.get("tags") else "Ninguno"
            
            tikwm_audio_url = meta.get("tikwm_audio_url")
            transcripcion = get_audio_and_transcribe(url_input, tmp, whisper_model, tikwm_audio_url)
            
            clasificacion = clasificar_con_ia(titulo, descripcion, transcripcion)
            
            with sqlite3.connect('tiktok_knowledge.db') as conn:
                conn.execute("""
                    INSERT INTO videos 
                    (url, title, author, description, tags, transcript, main_category, keywords) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    url_input, titulo, autor, descripcion, tags_originales, transcripcion,
                    clasificacion["categoria_principal"], 
                    ", ".join(clasificacion["palabras_clave"])
                ))
            
            # Generación del formato final integrado (evitando scrolls y divs complejos)
            st.session_state.markdown_output = f"""## 🔗 Origen y Metadatos
- **URL:** {url_input}
- **Título:** {titulo}
- **Autor:** {autor}
- **Categoría:** {clasificacion['categoria_principal']}
- **Tipo:** {clasificacion['tipo_contenido']}
- **Tags IA:** {', '.join(clasificacion['palabras_clave'])}
- **Hashtags Originales:** {tags_originales}

---

## 📝 Descripción Original
{descripcion}

---

## 🎙️ Transcripción del Audio
{transcripcion}"""

if st.session_state.markdown_output:
    st.success("¡Procesado y almacenado en SQLite exitosamente!")
    st.subheader("📦 Bloque Único de Exportación (Markdown)")
    
    # Renderizado directo dentro de un contenedor de código sin saltos de línea infinitos
    st.code(st.session_state.markdown_output, language="markdown")