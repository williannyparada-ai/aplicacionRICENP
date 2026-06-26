import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# Configuración de IA con selección automática de modelo
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Intentamos listar modelos disponibles y usar uno compatible
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Intentamos buscar gemini-1.5-flash, si no, tomamos el primero que funcione
    nombre_modelo = next((m for m in modelos if 'gemini-1.5-flash' in m), modelos[0] if modelos else 'gemini-pro')
    model = genai.GenerativeModel(nombre_modelo)
except Exception as e:
    st.error(f"Error de conexión con la IA: {e}")

# Memoria de sesión
if 'historico' not in st.session_state: st.session_state.historico = []
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

def procesar_con_ia(img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    prompt = "Extrae los datos de esta planilla de inspección. Devuelve un JSON plano con claves: {'Humedad': float, 'Impureza': float, 'Total Dañados': float, 'Total Part.': float}"
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}])
    # Limpiamos la respuesta para asegurar que sea solo JSON
    texto = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(texto)

# Sidebar: Identificación y Escáner
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Tu Nombre")
    f_fecha = st.date_input("Fecha de hoy", datetime.now())
    archivo = st.file_uploader("Subir foto planilla", type=['jpg', 'jpeg', 'png'])
    
    if archivo:
        img_pil = ImageOps.exif_transpose(Image.open(archivo))
        st.image(img_pil, use_container_width=True)
        if st.button("🤖 LEER PLANILLA"):
            with st.spinner("Procesando con IA..."):
                try:
                    st.session_state.datos_ia = procesar_con_ia(img_pil)
                    st.rerun() # Recargamos para que los campos se llenen
                except Exception as e: 
                    st.error(f"Error al leer: {e}")

# Formulario principal
st.title("🌾 Registro de Calidad Provencesa")
if not nombre_analista:
    st.warning("Por favor, ingresa tu nombre en la barra lateral.")
    st.stop()

d = st.session_state.datos_ia
with st.form("registro_maestro"):
    f_placa = st.text_input("Placa")
    
    col1, col2 = st.columns(2)
    respuestas = {
        "Humedad": col1.number_input("Humedad (%)", value=float(d.get("Humedad", 0.0))),
        "Impureza": col2.number_input("Impureza (%)", value=float(d.get("Impureza", 0.0))),
        "Total Dañados": col1.number_input("Total Dañados (%)", value=float(d.get("Total Dañados", 0.0))),
        "Total Part.": col2.number_input("Total Part. (%)", value=float(d.get("Total Part.", 0.0)))
    }
    
    f_estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de rechazo (si aplica):")
    
    # Este botón es vital para que el formulario funcione
    submit = st.form_submit_button("✅ REGISTRAR")

if submit:
    nuevo = {"Fecha": str(f_fecha), "Analista": nombre_analista, "Placa": f_placa, **respuestas, "Estatus": f_estatus}
    st.session_state.historico.append(nuevo)
    st.success("¡Vehículo registrado correctamente!")
    st.rerun()

# Historial y descarga
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    st.subheader("📋 Historial")
    st.dataframe(df)
    st.download_button("📥 Descargar Excel", df.to_csv(index=False), "registros.csv")
