import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Intentamos conectar con el modelo más capaz
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración: {e}")

# --- ESTADOS ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

# Lista de los 21 ítems definidos
ITEMS_CALIDAD = [
    "01. Humedad", "02. Impureza", "03. Germen Dañado", "04. Dañado Calor", "05. Dañado Insecto",
    "06. Infectados", "07. Total Dañados", "08. Part. Pequeños", "09. Granos Partidos", "10. Total Part.",
    "11. Cristalizados", "12. Mezcla Color", "13. Peso Vol", "14. Color", "15. Olor",
    "16. Aflatoxina", "17. Insectos V.", "18. Quemados", "19. Sensorial", "20. Semillas Obj.",
    "21. Fumonisina"
]

def procesar_planilla(img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    # Prompt optimizado para extraer los 21 puntos
    prompt = """Analiza esta planilla de control de calidad. 
    Extrae los valores numéricos de los 21 ítems enumerados (incluyendo Fumonisina al final).
    Si un valor es texto (ej: 'N', 'II'), ponlo como texto.
    Devuelve estrictamente un JSON con formato: 
    {"items": {"01": valor, "02": valor, ..., "21": valor}}."""
    
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    texto = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(texto)

# --- UI ---
st.title("🌾 Registro de Calidad Provencesa")

with st.sidebar:
    st.header("📸 Escáner")
    archivo = st.file_uploader("Subir foto planilla", type=['jpg', 'jpeg', 'png'])
    if archivo:
        img_pil = ImageOps.exif_transpose(Image.open(archivo))
        st.image(img_pil, use_container_width=True)
        if st.button("🤖 LEER LOS 21 ÍTEMS"):
            with st.spinner("Analizando 21 puntos..."):
                try:
                    resultado = procesar_planilla(img_pil)
                    st.session_state.datos_ia = resultado.get("items", {})
                    st.success("¡Lectura completa!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- FORMULARIO DINÁMICO ---
datos = st.session_state.datos_ia
with st.form("registro_maestro"):
    st.subheader("🔬 Resultados de Análisis (21 Ítems)")
    
    cols = st.columns(3)
    respuestas = {}
    for i, nombre in enumerate(ITEMS_CALIDAD):
        idx = str(i+1).zfill(2)
        val = datos.get(idx, 0.0)
        with cols[i % 3]:
            respuestas[nombre] = st.text_input(nombre, value=val)

    st.divider()
    f_estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de rechazo:")
    
    if st.form_submit_button("✅ REGISTRAR VEHÍCULO"):
        nuevo = {"Fecha": datetime.now().strftime("%Y-%m-%d"), **respuestas, "Estatus": f_estatus}
        st.session_state.historico.append(nuevo)
        st.success("Registrado correctamente.")
        st.rerun()

# --- HISTORIAL ---
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Descargar Excel", df.to_csv(index=False), "reporte_calidad.csv")
