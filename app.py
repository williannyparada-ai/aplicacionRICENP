import streamlit as st
import requests
import pandas as pd
import os
import re
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN ---
# Asegúrate de tener la clave en los Secrets de Streamlit o un respaldo aquí
try:
    API_KEY = st.secrets["OCR_API_KEY"]
except:
    API_KEY = "K83381284588957"

if 'datos_extraidos' not in st.session_state:
    st.session_state.datos_extraidos = {}

st.title("🌾 Registro de Calidad - Provencesa")

# --- 2. FUNCIÓN DE EXTRACCIÓN (Lógica de Auto-llenado) ---
def extraer_datos_ocr(texto):
    datos = {}
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", 
               "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", 
               "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", 
               "Quemados", "Sensorial", "Semillas Obj."]
    
    for nombre in nombres:
        # Busca el nombre del campo y captura números, puntos o comas siguientes
        patron = rf"{nombre}.*?(\d+[\.,]?\d*)"
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            datos[nombre] = match.group(1).replace(',', '.')
    return datos

# --- 3. BARRA LATERAL (OCR INTEGRADO) ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    
    if archivo and st.button("🤖 PROCESAR CON OCR"):
        with st.spinner("Procesando imagen..."):
            try:
                payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
                files = {'file': (archivo.name, archivo.getvalue())}
                response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                resultado = response.json()
                
                if not resultado.get("IsErroredOnProcessing"):
                    texto_ocr = resultado["ParsedResults"][0]["ParsedText"]
                    st.session_state.texto_ocr = texto_ocr
                    st.session_state.datos_extraidos = extraer_datos_ocr(texto_ocr)
                    st.success("¡Imagen procesada!")
                else:
                    st.error(f"Error OCR: {resultado.get('ErrorMessage')}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    if st.button("🧹 BORRAR TODO"):
        st.session_state.datos_extraidos = {}
        st.session_state.texto_ocr = ""
        st.rerun()

# --- 4. FORMULARIO ---
with st.form("registro_maestro"):
    if 'texto_ocr' in st.session_state and st.session_state.texto_ocr:
        with st.expander("Ver texto extraído por OCR"):
            st.text(st.session_state.texto_ocr)
            
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", "")
    
    c4, c5, c6 = st.columns(3)
    cereal = c4.selectbox("Cereal", ["", "Maíz Blanco", "Maíz Amarillo"])
    origen = c5.radio("Origen", ["Nacional", "Importado"], horizontal=True)
    destino = c6.text_input("Destino", "")

    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    respuestas = {}
    cols = st.columns(4)
    
    for i in range(20):
        with cols[i%4]:
            nombre = nombres[i]
            # Valor auto-detectado o 0.0
            val_auto = st.session_state.datos_extraidos.get(nombre, 0.0)
            respuestas[nombre] = st.number_input(f"{i+1}. {nombre}", value=float(val_auto))

    estatus = st.radio("Estatus Final:", ["Aprobado", "Rechazado"], horizontal=True)
    
    if st.form_submit_button("✅ REGISTRAR Y GUARDAR"):
        registro = {"Fecha": str(fecha), "Analista": analista, "Estatus": estatus, "Procedencia": procedencia, **respuestas}
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        
        df_nuevo = pd.DataFrame([registro])
        if os.path.exists(archivo_exc):
            df_existente = pd.read_excel(archivo_exc)
            pd.concat([df_existente, df_nuevo], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
        st.success(f"Guardado en {archivo_exc}")

# --- 5. DESCARGAS ---
st.divider()
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
