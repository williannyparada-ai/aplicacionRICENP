import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from datetime import datetime
import json
import io
import pandas as pd

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN ---
# Si esto falla, verifica que GOOGLE_API_KEY esté en los Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en configuración de API: {e}")

# --- ESTADOS ---
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

def procesar_planilla(img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    prompt = "Extrae los 21 ítems. Responde SOLO en JSON: {'items': {'01': 'val', ..., '21': 'val'}}"
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    return json.loads(response.text.replace('```json', '').replace('```', '').strip())

# --- UI ---
st.title("🌾 Registro de Calidad Provencesa")
archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])

if archivo and st.button("🤖 LEER PLANILLA"):
    with st.spinner("Procesando..."):
        try:
            img = ImageOps.exif_transpose(Image.open(archivo))
            res = procesar_planilla(img)
            st.session_state.datos_ia = res.get("items", {})
            st.rerun()
        except Exception as e:
            st.error(f"Error al leer imagen: {e}")

# --- FORMULARIO ---
with st.form("registro_final"):
    cols = st.columns(3)
    items_nombres = [f"{i+1:02d}. Ítem" for i in range(21)]
    for i, nombre in enumerate(items_nombres):
        idx = f"{i+1:02d}"
        with cols[i % 3]:
            st.text_input(nombre, value=str(st.session_state.datos_ia.get(idx, "0")))
    
    submitted = st.form_submit_button("✅ REGISTRAR")
