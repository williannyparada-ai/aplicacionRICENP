import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# Clave OCR
API_KEY = "K83381284588957"

# --- INICIALIZACIÓN DE ESTADO ---
if 'datos_extraidos' not in st.session_state:
    st.session_state.datos_extraidos = {}

# --- FUNCIÓN DE EXTRACCIÓN MEJORADA ---
def procesar_texto(texto):
    resultados = {}
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", 
               "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", 
               "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    for nombre in nombres:
        # Buscamos nombre -> saltamos paréntesis -> capturamos número
        # Esta regex busca el nombre, luego todo lo que no sea dígito, y finalmente captura el número
        patron = rf"{nombre}.*?\(.*?\).*?(\d+[.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        
        # Fallback: si no hay paréntesis
        if not match:
            patron_simple = rf"{nombre}.*?(\d+[.,]?\d*)"
            match = re.search(patron_simple, texto, re.IGNORECASE | re.DOTALL)
            
        if match:
            val_str = match.group(1).replace(',', '.')
            try:
                resultados[nombre] = float(val_str)
            except:
                pass
    return resultados

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR PLANILLA"):
        with st.spinner("Procesando..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            try:
                res = requests.post('https://api.ocr.space/parse/image', files=files, data=payload).json()
                if not res.get("IsErroredOnProcessing"):
                    texto = res["ParsedResults"][0]["ParsedText"]
                    st.session_state.datos_extraidos = procesar_texto(texto)
                    st.success("¡Datos extraídos!")
                    st.rerun() # FORZAMOS RECARGA PARA QUE EL FORMULARIO VEA LOS NUEVOS DATOS
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    # ... (cabecera como la tenías)
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    cols = st.columns(4)
    respuestas = {}
    
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            # AQUÍ ESTÁ EL TRUCO: leemos el estado de la sesión cada vez que se renderiza
            val = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(val), format="%.2f")

    if st.form_submit_button("✅ REGISTRAR"):
        st.success("Datos guardados.")
