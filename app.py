import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# Clave de OCR.space
API_KEY = "K83381284588957"

if 'datos_extraidos' not in st.session_state: st.session_state.datos_extraidos = {}
if 'texto_ocr' not in st.session_state: st.session_state.texto_ocr = ""

st.title("🌾 Registro de Calidad - Provencesa")

# --- FUNCIÓN DE EXTRACCIÓN MEJORADA ---
def procesar_texto(texto):
    resultados = {}
    # Nombres definidos en tu planilla
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", 
               "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", 
               "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    for nombre in nombres:
        # Buscamos la palabra clave y capturamos el número más cercano que no sea el Max X%
        # Explicación: busca el nombre, salta cualquier texto (incluso paréntesis) y busca el número
        patron = rf"{nombre}.*?(?:\(Max.*?\))?\s*(\d+[.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            valor_str = match.group(1).replace(',', '.')
            try:
                resultados[nombre] = float(valor_str)
            except:
                pass
    return resultados

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR PLANILLA"):
        with st.spinner("Leyendo con OCR..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            try:
                res = requests.post('https://api.ocr.space/parse/image', files=files, data=payload).json()
                if not res.get("IsErroredOnProcessing"):
                    texto = res["ParsedResults"][0]["ParsedText"]
                    st.session_state.texto_ocr = texto
                    st.session_state.datos_extraidos = procesar_texto(texto)
                    st.success("¡Datos detectados!")
                else:
                    st.error("Error en OCR.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", "")
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    cols = st.columns(4)
    respuestas = {}
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            val = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(val), format="%.2f")

    if st.form_submit_button("✅ REGISTRAR"):
        st.success("Datos listos para enviar a base de datos.")

# --- DEBUG ---
with st.expander("Ver texto detectado por OCR"):
    st.write(st.session_state.texto_ocr)
