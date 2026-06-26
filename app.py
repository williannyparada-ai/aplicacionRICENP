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

st.title("🌾 Registro de Calidad - Provencesa")

# --- FUNCIÓN DE EXTRACCIÓN ROBUSTA ---
def extraer_todo(texto):
    resultados = {}
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", 
               "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", 
               "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    for nombre in nombres:
        # Busca el nombre del campo, y luego busca el primer número (decimal o entero) que aparece después
        # .*? significa "cualquier cosa hasta encontrar lo siguiente"
        patron = rf"{nombre}.*?(\d+[.,]\d+)"
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            valor = match.group(1).replace(',', '.')
            resultados[nombre] = float(valor)
    return resultados

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🚀 PROCESAR PLANILLA"):
        with st.spinner("Procesando imagen..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            try:
                res = requests.post('https://api.ocr.space/parse/image', files=files, data=payload).json()
                if not res.get("IsErroredOnProcessing"):
                    texto_ocr = res["ParsedResults"][0]["ParsedText"]
                    st.session_state.datos_extraidos = extraer_todo(texto_ocr)
                    st.session_state.texto_crudo = texto_ocr # Para debug
                    st.success("¡Datos detectados!")
                else:
                    st.error("Error al procesar.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    # Restauramos cabecera
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia")
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos partidos", "Total Granos partidos", "Cristalizados", "Mezcla de Color", "Peso Volumetrico", "Color", "Olor", "Aflatoxina", "Insectos Vivos", "Granos Quemados", "Sensorial", "Semillas Obj."]
    
    cols = st.columns(4)
    respuestas = {}
    for i, nombre in enumerate(nombres):
        with cols[i%4]:
            # El valor viene de la extracción o es 0.0
            val_default = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(val_default), format="%.2f")

    if st.form_submit_button("✅ REGISTRAR"):
        st.success("Registro guardado exitosamente.")

# --- DEBUG ---
with st.expander("Ver texto crudo (para depuración)"):
    if 'texto_crudo' in st.session_state:
        st.text(st.session_state.texto_crudo)
