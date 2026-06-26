import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from datetime import datetime
import json
import io
import pandas as pd

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos 'gemini-1.5-flash' que es el estándar actual más compatible
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración: {e}")

# --- 2. VARIABLES DE SESIÓN ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

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
    prompt = "Extrae los 21 valores de la planilla. Devuelve JSON: {'items': {'01': 'valor', ..., '21': 'valor'}}"
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    return json.loads(response.text.replace('```json', '').replace('```', '').strip())

# --- 3. UI ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Nombre y Apellido")
    fecha_hoy = st.date_input("Fecha", datetime.now())
    archivo = st.file_uploader("Subir foto", type=['jpg', 'jpeg', 'png'])
    if archivo:
        img_pil = ImageOps.exif_transpose(Image.open(archivo))
        if st.button("🤖 LEER LOS 21 ÍTEMS"):
            with st.spinner("Analizando..."):
                try:
                    res = procesar_planilla(img_pil)
                    st.session_state.datos_ia = res.get("items", {})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error IA: {e}")

st.title("🌾 Registro de Calidad Provencesa")
if not nombre_analista:
    st.warning("Ingresa tu nombre.")
    st.stop()

# --- 4. FORMULARIO CON BOTÓN INTEGRADO ---
datos = st.session_state.datos_ia
with st.form("registro_maestro"):
    cols = st.columns(3)
    respuestas = {}
    for i, nombre in enumerate(ITEMS_CALIDAD):
        idx = str(i+1).zfill(2)
        val = datos.get(idx, "0.0")
        with cols[i % 3]:
            respuestas[nombre] = st.text_input(nombre, value=str(val))
    
    f_estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"], horizontal=True)
    # EL BOTÓN DEBE ESTAR DENTRO DEL FORM
    submitted = st.form_submit_button("✅ REGISTRAR VEHÍCULO")

if submitted:
    nuevo = {"Fecha": str(fecha_hoy), "Analista": nombre_analista, **respuestas, "Estatus": f_estatus}
    st.session_state.historico.append(nuevo)
    st.success("Registrado.")
    st.rerun()
