import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="App Calidad", layout="wide")

API_KEY = "K83381284588957"

if 'datos_finales' not in st.session_state:
    st.session_state.datos_finales = {}

def extraer_datos_precisos(texto):
    """Extrae valores buscando específicamente después de cada etiqueta."""
    resultados = {}
    
    # Diccionario de mapeo: Nombre del campo -> Regex para encontrar su valor
    # Usamos patrones que buscan la etiqueta y el número justo al lado o abajo
    mapeo = {
        "Humedad": r"Humedad.*?(\d+[\.,]\d+)",
        "Impureza": r"Impureza.*?(\d+[\.,]\d+)",
        "Germen Dañado": r"Germen Dañado.*?(\d+[\.,]\d+)",
        "Dañado Calor": r"Dañado por Calor.*?(\d+[\.,]\d+)",
        "Dañado Insecto": r"Dañado por Insectos.*?(\d+[\.,]\d+)",
        "Infectados": r"Granos Infectados.*?(\d+[\.,]\d+)",
        "Total Dañados": r"Total de Granos Dañados.*?(\d+[\.,]\d+)",
        "Partidos Peq.": r"Granos Partido Pequeños.*?(\d+[\.,]\d+)",
        "Granos partidos": r"Granos partidos.*?(\d+[\.,]\d+)",
        "Total Granos partidos": r"Total Granos partidos.*?(\d+[\.,]\d+)",
        "Cristalizados": r"Granos Cristalizados.*?(\d+[\.,]\d+)",
        "Mezcla de Color": r"Mezcla de Color.*?(\d+[\.,]\d+)",
        "Peso Volumetrico": r"Peso Volumetrico.*?(\d+[\.,]\d+)",
    }
    
    for campo, patron in mapeo.items():
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            resultados[campo] = float(match.group(1).replace(',', '.'))
    return resultados

# --- INTERFAZ ---
with st.sidebar:
    archivo = st.file_uploader("Subir imagen", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR"):
        with st.spinner("Leyendo con precisión..."):
            res = requests.post('https://api.ocr.space/parse/image', 
                                files={'file': (archivo.name, archivo.getvalue())}, 
                                data={'apikey': API_KEY, 'language': 'spa'}).json()
            
            if "ParsedResults" in res:
                texto = res["ParsedResults"][0]["ParsedText"]
                st.session_state.datos_finales = extraer_datos_precisos(texto)
                st.rerun()

with st.form("registro"):
    cols = st.columns(4)
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", 
               "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", 
               "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico"]
    
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            val = st.session_state.datos_finales.get(nombre, 0.0)
            st.number_input(f"{i+1}. {nombre}", value=val, format="%.2f")
    
    st.form_submit_button("✅ REGISTRAR")
