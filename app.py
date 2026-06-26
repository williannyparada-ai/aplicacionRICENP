import streamlit as st
import requests
import json
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
OCR_API_KEY = "K83381284588957" # <--- PEGA TU CLAVE AQUÍ

st.set_page_config(page_title="App Calidad Provencesa", layout="wide")

st.title("🌾 Registro de Calidad - Provencesa")

# --- FUNCIÓN DE OCR ---
def procesar_con_ocr(archivo):
    url = "https://api.ocr.space/parse/image"
    files = {"file": archivo.getvalue()}
    payload = {"apikey": OCR_API_KEY, "language": "spa", "isOverlayRequired": False}
    
    response = requests.post(url, files=files, data=payload)
    result = response.json()
    
    if result.get("IsErroredOnProcessing"):
        return None
    return result["ParsedResults"][0]["ParsedText"]

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR SIN GOOGLE"):
        with st.spinner("Leyendo planilla..."):
            texto_extraido = procesar_con_ocr(archivo)
            if texto_extraido:
                st.session_state.texto_raw = texto_extraido
                st.success("¡Texto extraído con éxito!")
            else:
                st.error("Error al procesar la imagen.")

# --- FORMULARIO (Mismo de antes) ---
with st.form("registro"):
    # Aquí puedes añadir los campos igual que antes...
    st.write("Datos procesados listos para revisar.")
    if st.form_submit_button("Guardar"):
        st.success("Guardado correctamente.")
