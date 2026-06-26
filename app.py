import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Provencesa", layout="wide", page_icon="🌾")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Configura tu GOOGLE_API_KEY en los Secrets.")

# --- MEMORIA (Privada por sesión) ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

def procesar_con_ia(img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    response = model.generate_content(["Extrae datos de esta planilla en JSON.", {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    return json.loads(response.text.replace('```json', '').replace('```', ''))

# --- SIDEBAR: IDENTIFICACIÓN Y ESCÁNER ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Tu Nombre")
    archivo = st.file_uploader("Subir foto planilla", type=['jpg', 'jpeg', 'png'])
    if archivo:
        img_pil = ImageOps.exif_transpose(Image.open(archivo))
        st.image(img_pil, use_container_width=True)
        if st.button("🤖 LEER PLANILLA"):
            with st.spinner("Procesando..."):
                try:
                    st.session_state.datos_ia = procesar_con_ia(img_pil)
                    st.rerun()
                except: st.error("Error al leer.")

# --- FORMULARIO ---
st.title("🌾 Registro de Calidad Provencesa")
if not nombre_analista:
    st.warning("Ingresa tu nombre en el menú lateral.")
    st.stop()

items = st.session_state.datos_ia.get('items', {})
with st.form("registro_maestro"):
    f_placa = st.text_input("Placa", value=st.session_state.datos_ia.get('cabecera', {}).get('placa', ''))
    
    c1, c2, c3, c4 = st.columns(4)
    respuestas = {}
    nombres = ["Humedad", "Impureza", "Total Dañados", "Total Part."]
    for i, nombre in enumerate(nombres):
        respuestas[nombre] = c1.number_input(nombre, value=float(items.get(nombre, 0.0)))

    f_estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de rechazo:")
    
    if st.form_submit_button("✅ REGISTRAR Y DESCARGAR"):
        # Lógica COVENIN
        d, i, p = respuestas["Total Dañados"], respuestas["Impureza"], respuestas["Total Part."]
        clase = "CLASE I" if d <= 6 and i <= 2 and p <= 3 else ("CLASE II" if d <= 8 and p <= 5 else "CLASE III")
        
        nuevo = {"Placa": f_placa, "Estatus": f_estatus, "Clase": clase, **respuestas}
        st.session_state.historico.append(nuevo)
        
        # Generar PDF local
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, f"REPORTE: {clase} | Placa: {f_placa}", ln=True)
        for k, v in nuevo.items(): pdf.cell(0, 10, f"{k}: {v}", ln=True)
        st.session_state.pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.rerun()

# --- DESCARGAS ---
if 'pdf_bytes' in st.session_state:
    st.download_button("📥 Descargar Mi Reporte PDF", st.session_state.pdf_bytes, "reporte.pdf")

if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    st.dataframe(df)
    st.download_button("📥 Descargar Mi Excel del Día", df.to_csv(index=False), "mis_registros.csv")
