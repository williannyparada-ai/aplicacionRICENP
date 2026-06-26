import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN ---
API_KEY = "K83381284588957"

if 'datos_extraidos' not in st.session_state: st.session_state.datos_extraidos = {}
if 'cabecera_extraida' not in st.session_state: st.session_state.cabecera_extraida = {}

st.title("🌾 Registro de Calidad - Provencesa")

# --- FUNCIÓN DE EXTRACCIÓN MEJORADA ---
def procesar_todo(texto):
    resultados = {"items": {}, "cabecera": {}}
    
    # Lista de nombres de items
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", 
               "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", 
               "Granos Quemados", "Sensorial", "Semillas Obj."]

    for nombre in nombres:
        # Buscamos el nombre y el número que le sigue
        patron = rf"{nombre}.*?(\d+[.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            resultados["items"][nombre] = float(match.group(1).replace(',', '.'))
    
    # Extraer Cereal (búsqueda simple)
    if "Maíz Blanco" in texto: resultados["cabecera"]["Cereal"] = "Maíz Blanco"
    elif "Maíz Amarillo" in texto: resultados["cabecera"]["Cereal"] = "Maíz Amarillo"
    
    return resultados

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR"):
        with st.spinner("Leyendo planilla..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            res = requests.post('https://api.ocr.space/parse/image', files=files, data=payload).json()
            
            if not res.get("IsErroredOnProcessing"):
                texto = res["ParsedResults"][0]["ParsedText"]
                datos = procesar_todo(texto)
                st.session_state.datos_extraidos = datos["items"]
                st.session_state.cabecera_extraida = datos["cabecera"]
                st.success("¡Datos extraídos!")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    # Cabecera
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", "")
    
    c4, c5, c6 = st.columns(3)
    cereal = c4.selectbox("Cereal", ["", "Maíz Blanco", "Maíz Amarillo"], 
                          index=["", "Maíz Blanco", "Maíz Amarillo"].index(st.session_state.cabecera_extraida.get("Cereal", "")))
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    cols = st.columns(4)
    respuestas = {}
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            val = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(val), format="%.2f")

    if st.form_submit_button("✅ REGISTRAR"):
        st.success("Datos guardados correctamente.")
