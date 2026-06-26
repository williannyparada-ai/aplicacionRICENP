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

if 'datos_extraidos' not in st.session_state:
    st.session_state.datos_extraidos = {}
if 'texto_ocr' not in st.session_state:
    st.session_state.texto_ocr = ""

st.title("🌾 Registro de Calidad - Provencesa")

# --- FUNCIÓN DE EXTRACCIÓN INTELIGENTE ---
def extraer_datos_ocr(texto):
    datos = {}
    # Nombres definidos en tu código
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", 
               "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", 
               "Quemados", "Sensorial", "Semillas Obj."]
    
    for nombre in nombres:
        # El patrón busca el nombre, luego cualquier cosa (espacios, saltos de línea, guiones)
        # y captura el número que le sigue
        patron = rf"{nombre}.*?(\d+[.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            # Reemplaza coma por punto para convertir a número correctamente
            valor_str = match.group(1).replace(',', '.')
            try:
                datos[nombre] = float(valor_str)
            except:
                pass
    return datos

# --- BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    
    if archivo and st.button("🚀 PROCESAR PLANILLA"):
        with st.spinner("Procesando..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            
            try:
                response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                resultado = response.json()
                
                if not resultado.get("IsErroredOnProcessing"):
                    texto_completo = resultado["ParsedResults"][0]["ParsedText"]
                    st.session_state.texto_ocr = texto_completo
                    # Ejecuta la extracción
                    st.session_state.datos_extraidos = extraer_datos_ocr(texto_completo)
                    st.success("¡Datos detectados!")
                else:
                    st.error("Error al procesar.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    # ... (tus inputs de cabecera como antes)
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    respuestas = {}
    cols = st.columns(4)
    
    for i in range(20):
        with cols[i%4]:
            nombre = nombres[i]
            # Usa el dato extraído si existe, sino 0.0
            valor_default = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(valor_default))

    if st.form_submit_button("✅ REGISTRAR"):
        # ... (tu lógica de guardado en Excel que ya tenías)
        st.success("¡Registrado!")
