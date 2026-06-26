import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd

# Configuración
st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# Configuración IA Robusta
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos gemini-1.5-flash directamente
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de conexión IA: {e}")

# Memoria de sesión
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

def procesar_con_ia(img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    prompt = "Extrae los datos de la planilla en formato JSON con claves: {'items': {'Humedad': float, 'Impureza': float, 'Total Dañados': float, 'Total Part.': float}}"
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    return json.loads(response.text.replace('```json', '').replace('```', ''))

# Sidebar
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Tu Nombre")
    f_fecha = st.date_input("Fecha de hoy", datetime.now())
    archivo = st.file_uploader("Subir foto planilla", type=['jpg', 'jpeg', 'png'])
    if archivo:
        img_pil = ImageOps.exif_transpose(Image.open(archivo))
        st.image(img_pil, use_container_width=True)
        if st.button("🤖 LEER PLANILLA"):
            with st.spinner("Procesando..."):
                try:
                    st.session_state.datos_ia = procesar_con_ia(img_pil)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# Formulario
st.title("🌾 Registro de Calidad Provencesa")
if not nombre_analista:
    st.warning("Ingresa tu nombre.")
    st.stop()

items = st.session_state.datos_ia.get('items', {})
with st.form("registro_maestro"):
    f_placa = st.text_input("Placa")
    
    col1, col2 = st.columns(2)
    respuestas = {
        "Humedad": col1.number_input("Humedad", value=float(items.get("Humedad", 0.0))),
        "Impureza": col2.number_input("Impureza", value=float(items.get("Impureza", 0.0))),
        "Total Dañados": col1.number_input("Total Dañados", value=float(items.get("Total Dañados", 0.0))),
        "Total Part.": col2.number_input("Total Part.", value=float(items.get("Total Part.", 0.0)))
    }
    
    f_estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo:")
    
    if st.form_submit_button("✅ REGISTRAR"):
        nuevo = {"Fecha": str(f_fecha), "Analista": nombre_analista, "Placa": f_placa, **respuestas, "Estatus": f_estatus}
        st.session_state.historico.append(nuevo)
        st.success("Registrado.")
        st.rerun()

# Historial y descarga
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    st.dataframe(df)
    st.download_button("📥 Descargar Excel", df.to_csv(index=False), "registros.csv")
