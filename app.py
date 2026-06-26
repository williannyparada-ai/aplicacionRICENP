import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="App Calidad", layout="wide")

# Clave OCR
API_KEY = "K83381284588957"

if 'datos_finales' not in st.session_state:
    st.session_state.datos_finales = {}

def limpiar_y_extraer(texto):
    resultados = {}
    # Esta lista debe coincidir exactamente con los nombres en tu interfaz
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", 
               "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", 
               "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    # Dividir el texto en líneas para procesar mejor
    lineas = texto.split('\n')
    
    for i, nombre in enumerate(nombres):
        # Buscamos una línea que contenga el nombre del campo
        for linea in lineas:
            if nombre.lower() in linea.lower():
                # Buscamos números en esa línea que no estén dentro de paréntesis
                # Esto es clave para ignorar el (Max 24%)
                linea_limpia = re.sub(r'\(.*?\)', '', linea)
                numeros = re.findall(r'\d+[.,]\d+', linea_limpia)
                if numeros:
                    resultados[nombre] = float(numeros[0].replace(',', '.'))
    return resultados

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir imagen", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR"):
        with st.spinner("Procesando..."):
            payload = {'apikey': API_KEY, 'language': 'spa'}
            files = {'file': (archivo.name, archivo.getvalue())}
            res = requests.post('https://api.ocr.space/parse/image', files=files, data=payload).json()
            
            if "ParsedResults" in res:
                texto = res["ParsedResults"][0]["ParsedText"]
                st.session_state.datos_finales = limpiar_y_extraer(texto)
                st.rerun()

# --- FORMULARIO ---
with st.form("registro"):
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    cols = st.columns(4)
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            # Usamos el valor extraído o 0.0
            valor = st.session_state.datos_finales.get(nombre, 0.0)
            st.number_input(f"{i+1}. {nombre}", value=float(valor), format="%.2f", key=f"input_{i}")

    if st.form_submit_button("✅ REGISTRAR"):
        st.success("Guardado.")
