import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN ---
# Usamos tu clave de OCR.space
API_KEY = "K83381284588957"

# Inicializar estado para guardar los datos encontrados
if 'datos_extraidos' not in st.session_state:
    st.session_state.datos_extraidos = {}
if 'texto_ocr' not in st.session_state:
    st.session_state.texto_ocr = ""

st.title("🌾 Registro de Calidad - Provencesa")

# --- 2. FUNCIÓN DE AUTO-LLENADO ---
def procesar_texto_ocr(texto):
    """Busca los números en el texto basándose en los nombres de los campos."""
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", 
               "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", 
               "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", 
               "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    
    resultados = {}
    for nombre in nombres:
        # Regex: Busca el nombre y captura el número que le sigue (soporta punto y coma)
        patron = rf"{nombre}.*?(\d+[\.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            # Reemplazamos coma por punto para que el float() de Python no falle
            resultados[nombre] = float(match.group(1).replace(',', '.'))
    return resultados

# --- 3. BARRA LATERAL ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    
    if archivo and st.button("🚀 PROCESAR SIN GOOGLE"):
        with st.spinner("Procesando con OCR..."):
            payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
            files = {'file': (archivo.name, archivo.getvalue())}
            
            try:
                response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                resultado = response.json()
                
                if not resultado.get("IsErroredOnProcessing"):
                    texto_completo = resultado["ParsedResults"][0]["ParsedText"]
                    st.session_state.texto_ocr = texto_completo
                    # Extraer y guardar automáticamente
                    st.session_state.datos_extraidos = procesar_texto_ocr(texto_completo)
                    st.success("Datos procesados listos para revisar.")
                else:
                    st.error("Error al procesar la imagen.")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("🧹 Limpiar"):
        st.session_state.datos_extraidos = {}
        st.session_state.texto_ocr = ""
        st.rerun()

# --- 4. FORMULARIO ---
with st.form("registro_maestro"):
    if st.session_state.texto_ocr:
        with st.expander("Ver texto extraído"):
            st.text(st.session_state.texto_ocr)
    
    # Campos de cabecera
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia")
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", 
               "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", 
               "Quemados", "Sensorial", "Semillas Obj."]
    
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            nombre = nombres[i]
            # Si el OCR encontró un valor, lo usa; si no, pone 0.0
            valor_default = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(valor_default))

    estatus = st.radio("Estatus Final:", ["Aprobado", "Rechazado"], horizontal=True)
    
    if st.form_submit_button("Guardar"):
        # Guardado en Excel
        registro = {"Fecha": str(fecha), "Analista": analista, "Estatus": estatus, **respuestas}
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        df = pd.DataFrame([registro])
        
        if os.path.exists(archivo_exc):
            pd.concat([pd.read_excel(archivo_exc), df], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df.to_excel(archivo_exc, index=False)
        st.success("¡Guardado!")

# --- 5. DESCARGAS ---
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
