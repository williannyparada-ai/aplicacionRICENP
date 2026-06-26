import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from datetime import datetime
import json
import io
import pandas as pd

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN DE SEGURIDAD ---
try:
    # Asegúrate de que esta variable coincida exactamente con lo que pusiste en Secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración (Revisa los Secrets): {e}")

# --- ESTADOS ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

# --- SIDEBAR (Nombre y Fecha restaurados) ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Tu Nombre", key="nombre")
    fecha_hoy = st.date_input("Fecha de hoy", datetime.now())
    st.divider()
    archivo = st.file_uploader("Subir foto planilla", type=['jpg', 'jpeg', 'png'])
    
    if archivo and st.button("🤖 LEER PLANILLA"):
        with st.spinner("Analizando..."):
            try:
                img_pil = ImageOps.exif_transpose(Image.open(archivo))
                img_byte_arr = io.BytesIO()
                img_pil.save(img_byte_arr, format='JPEG')
                prompt = "Extrae los 21 ítems. Responde SOLO en JSON: {'items': {'01': 'val', ..., '21': 'val'}}"
                response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
                res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                st.session_state.datos_ia = res.get("items", {})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO ---
st.title("🌾 Registro de Calidad Provencesa")
if not nombre_analista:
    st.warning("Por favor, coloca tu nombre en la barra lateral.")
else:
    with st.form("registro_maestro"):
        st.subheader(f"Analista: {nombre_analista} | Fecha: {fecha_hoy}")
        cols = st.columns(3)
        respuestas = {}
        for i in range(21):
            idx = f"{i+1:02d}"
            with cols[i % 3]:
                respuestas[idx] = st.text_input(f"Ítem {idx}", value=str(st.session_state.datos_ia.get(idx, "0")))
        
        submitted = st.form_submit_button("✅ REGISTRAR VEHÍCULO")
        if submitted:
            st.success("¡Datos registrados!")
