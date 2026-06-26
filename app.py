import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN OCR.SPACE ---
# Asegúrate de tener tu clave en los Secrets de Streamlit
try:
    API_KEY = st.secrets["OCR_API_KEY"]
except:
    API_KEY = "K83381284588957" # Clave de respaldo

if 'datos_ia' not in st.session_state: 
    st.session_state.datos_ia = {'cabecera': {}, 'items': {}}

st.title("🌾 Registro de Calidad - Provencesa")

# --- 2. BARRA LATERAL (OCR INTEGRADO) ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    
    if archivo and st.button("🤖 PROCESAR CON OCR"):
        with st.spinner("Leyendo imagen con OCR..."):
            try:
                # Lógica de envío a OCR.space
                payload = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
                files = {'file': (archivo.name, archivo.getvalue())}
                response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                resultado = response.json()
                
                if not resultado.get("IsErroredOnProcessing"):
                    texto = resultado["ParsedResults"][0]["ParsedText"]
                    st.success("¡Imagen leída!")
                    # Nota: Aquí guardamos el texto crudo; como no tenemos IA para limpiar, 
                    # el usuario puede copiar/pegar o nosotros procesar el texto con código simple.
                    st.session_state.texto_ocr = texto
                else:
                    st.error(f"Error: {resultado.get('ErrorMessage')}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    st.divider()
    if st.button("🧹 BORRAR TODO"):
        st.session_state.datos_ia = {'cabecera': {}, 'items': {}}
        st.session_state.texto_ocr = ""
        st.rerun()

# --- 3. FORMULARIO ---
with st.form("registro_maestro"):
    # Si hubo OCR, podemos mostrarlo aquí para referencia
    if 'texto_ocr' in st.session_state:
        with st.expander("Ver texto extraído por OCR"):
            st.text(st.session_state.texto_ocr)
    
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", "")
    
    # ... (resto de tus campos como en tu código original)
    cereal = st.selectbox("Cereal", ["", "Maíz Blanco", "Maíz Amarillo"])
    
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            respuestas[nombres[i]] = st.number_input(f"{i+1}. {nombres[i]}", value=0.0)

    estatus = st.radio("Estatus Final:", ["Aprobado", "Rechazado"], horizontal=True)
    
    if st.form_submit_button("✅ REGISTRAR Y GUARDAR"):
        registro = {"Fecha": str(fecha), "Analista": analista, "Estatus": estatus, **respuestas}
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        
        df_nuevo = pd.DataFrame([registro])
        if os.path.exists(archivo_exc):
            df_existente = pd.read_excel(archivo_exc)
            pd.concat([df_existente, df_nuevo], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
        st.success(f"Guardado en {archivo_exc}")
