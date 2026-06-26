import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import json
import pandas as pd
import os

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_vision = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_vision[0]) if modelos_vision else None
except: model = None

# --- ESTADO ---
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {'cabecera': {}, 'items': {}}

st.title("🌾 Registro de Información - Provencesa")

# 1. ENTRADA
col1, col2 = st.columns(2)
analista = col1.text_input("Nombre y Apellido del Analista")
fecha = col2.date_input("Fecha de Inspección")

# 2. ESCÁNER
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR PLANILLA"):
        with st.spinner("IA analizando..."):
            try:
                img = Image.open(archivo)
                prompt = "Extrae los datos en formato JSON estricto: {'cabecera': {'placa':'', 'silo':'', ...}, 'items': {'01': 0.0, '02': 0.0, ...}}"
                res = model.generate_content([prompt, img])
                st.session_state.datos_ia = json.loads(res.text.replace('```json','').replace('```',''))
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# 3. FORMULARIO SEGURO
with st.form("registro_maestro"):
    d = st.session_state.datos_ia
    items = d.get('items', {})
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", 
               "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.",
               "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina",
               "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            val = items.get(str(i+1).zfill(2), 0.0)
            # Limpieza segura de datos para evitar ValueError
            try:
                valor_seguro = float(val)
            except:
                valor_seguro = 0.0
            respuestas[nombres[i]] = st.number_input(f"{i+1}. {nombres[i]}", value=valor_seguro)

    # BOTÓN OBLIGATORIO DENTRO DEL FORM
    submit = st.form_submit_button("✅ REGISTRAR Y GUARDAR")

    if submit:
        st.success("Registrado correctamente.")
        # Aquí va tu lógica de guardado en Excel...
