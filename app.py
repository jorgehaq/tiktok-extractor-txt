import streamlit as st
import sqlite3
import json
import subprocess
import tempfile
import os
import whisper

# -- 1. CONFIGURACIÓN DEL ESCENARIO (DB y Modelos) --

def init_db():
    """El diario de bolsillo: Crea la tabla si no existe."""
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
    """Carga el modelo una sola vez para no congelar la app."""
    return whisper.load_model("base", device="cpu")

# -- 2. LOS LOADERS (Extracción) --

def get_full_metadata(url, tmp_dir):
    """Extrae todo como si lo vieras en el teléfono."""
    cmd = [
        "yt-dlp", "--no-playlist", "--dump-json", "--quiet",
        "-o", os.path.join(tmp_dir, "%(id)s.%(ext)s"), url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        return json.loads(result.stdout.strip().splitlines()[-1])
    return {}

def get_audio_and_transcribe(url, tmp_dir, model):
    """Descarga el audio y lo pasa por Whisper."""
    cmd = [
        "yt-dlp", "--extract-audio", "--audio-format", "mp3", "--quiet",
        "-o", os.path.join(tmp_dir, "audio.%(ext)s"), url
    ]
    subprocess.run(cmd)
    
    audio_path = os.path.join(tmp_dir, "audio.mp3")
    if os.path.exists(audio_path):
        result = model.transcribe(audio_path, fp16=False)
        return result.get("text", "").strip()
    return ""

# -- 3. EL CEREBRO (Clasificación Controlada) --

def clasificar_con_ia(titulo, descripcion, transcripcion):
    """
    Aquí conectas tu API (OpenAI, Gemini, etc).
    El truco está en el PROMPT estricto para evitar crecimiento arbóreo infinito.
    """
    prompt = f"""
    Actúa como un bibliotecario experto. Analiza este video de TikTok:
    Título: {titulo}
    Descripción: {descripcion}
    Transcripción: {transcripcion}
    
    Devuelve ÚNICAMENTE un JSON con esta estructura:
    {{
        "categoria_principal": "Elige SOLO UNA de: [Tecnología, Productividad, Tutoriales, Ocio, Finanzas, Otro]",
        "tipo_contenido": "Elige SOLO UNO de: [Tip/Truco, Reflexión, Noticia, Comedia, Review]",
        "palabras_clave": ["keyword1", "keyword2", "keyword3"] 
    }}
    """
    
    # SIMULACIÓN (Reemplaza esto con tu llamada real a la API de IA)
    # respuesta_ia = llm.generate(prompt)
    respuesta_simulada = {
        "categoria_principal": "Tecnología",
        "tipo_contenido": "Tip/Truco",
        "palabras_clave": ["python", "scripts", "automatización"]
    }
    return respuesta_simulada

# -- 4. LA INTERFAZ (Streamlit) --

st.set_page_config(page_title="TikTok Brain", layout="wide")
init_db()
whisper_model = load_whisper()

st.title("🧠 TikTok Knowledge Extractor")

url_input = st.text_input("🔗 Pega la URL del TikTok:")

if st.button("🚀 Extraer y Clasificar"):
    if url_input:
        with st.spinner("Trabajando en bambalinas..."):
            with tempfile.TemporaryDirectory() as tmp:
                # 1. Extraer Metadata
                meta = get_full_metadata(url_input, tmp)
                titulo = meta.get("title", "")
                descripcion = meta.get("description", "")
                autor = meta.get("uploader", "")
                tags_originales = ", ".join(meta.get("tags", []))
                
                # 2. Transcribir Audio
                transcripcion = get_audio_and_transcribe(url_input, tmp, whisper_model)
                
                # 3. Clasificación de IA Controlada
                clasificacion = clasificar_con_ia(titulo, descripcion, transcripcion)
                
                # 4. Guardar en SQLite
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
                
                # 5. Mostrar Resultados (El Output Rápido)
                st.success("¡Procesado y guardado!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📦 Clasificación AI")
                    st.write(f"**Cajón Principal:** {clasificacion['categoria_principal']}")
                    st.write(f"**Tipo:** {clasificacion['tipo_contenido']}")
                    st.write(f"**Tags IA:** {', '.join(clasificacion['palabras_clave'])}")
                    st.write(f"**Hashtags Originales:** {tags_originales}")
                
                with col2:
                    st.subheader("📝 Contenido")
                    st.text_area("Descripción Original", descripcion, height=150)
                    st.text_area("Transcripción del Audio", transcripcion, height=150)
                
                # 6. Módulo de Exportación (El "Contenedor de Carga")
                payload_markdown = f"""## 🔗 Origen y Metadatos
- **URL:** {url_input}
- **Clasificación:** {clasificacion["categoria_principal"]} | {", ".join(clasificacion["palabras_clave"])}

---

## 📝 Descripción Original
{descripcion}

---

## 🎙️ Transcripción del Audio (Isótopo Puro)
{transcripcion}
"""
                st.divider()
                st.subheader("📦 Empaquetado para Exportación (Markdown)")
                st.caption("Haz clic en el ícono de copiar en la esquina superior derecha del cuadro inferior. Todo quedará listo para pegar en tu archivo .md")
                st.code(payload_markdown, language="markdown")