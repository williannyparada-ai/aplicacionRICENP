import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import json
import pandas as pd
import os

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0]) if modelos else None
except: model = None

# --- ESTADO ---
if 'datos_ia' not in st.session_state: 
    st.session_state.datos_ia = {'cabecera': {}, 'items': {}}

st.title("🌾 Registro de Calidad - Provencesa")

# --- ESCÁNER ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR PLANILLA"):
        with st.spinner("Analizando..."):
            try:
                # Prompt ajustado para ignorar Cereal/Origen y enfocarse en datos numéricos
                prompt = 'Extrae los datos en JSON. Ignora Cereal y Origen. Estructura: {"cabecera": {"Procedencia":"", "Destino":"", "Contrato":"", "Documento":"", "Placa":"", "Silo":""}, "items": {"01": 0.0, ...}}'
                res = model.generate_content([prompt, Image.open(archivo)])
                texto = res.text.replace('```json', '').replace('```', '').strip()
                st.session_state.datos_ia = json.loads(texto)
                st.rerun()
            except Exception as e:
                st.error(f"Error procesando: {e}")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    cab = st.session_state.datos_ia.get('cabecera', {})
    items = st.session_state.datos_ia.get('items', {})
    
    # Cabecera
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", cab.get("Procedencia", ""))
    
    # Nuevos desplegables
    c4, c5, c6 = st.columns(3)
    cereal = c4.selectbox("Cereal", ["", "Maíz Blanco", "Maíz Amarillo"], index=0)
    origen = c5.radio("Origen", ["Nacional", "Importado"], horizontal=True)
    destino = c6.text_input("Destino", cab.get("Destino", ""))
    
    c7, c8, c9, c10 = st.columns(4)
    contrato = c7.text_input("N Contrato", cab.get("Contrato", ""))
    documento = c8.text_input("Documento", cab.get("Documento", ""))
    placa = c9.text_input("Placa", cab.get("Placa", ""))
    silo = c10.text_input("Silo", cab.get("Silo", ""))

    # Resultados
    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            val = items.get(str(i+1).zfill(2), 0.0)
            try: v_f = float(val)
            except: v_f = 0.0
            respuestas[nombres[i]] = st.number_input(f"{i+1}. {nombres[i]}", value=v_f)

    estatus = st.radio("Estatus Final:", ["Aprobado", "Rechazado"], horizontal=True)
    
    # BOTÓN OBLIGATORIO
    if st.form_submit_button("✅ REGISTRAR Y GUARDAR"):
        registro = {
            "Fecha": str(fecha), "Analista": analista, "Procedencia": procedencia, "Cereal": cereal,
            "Origen": origen, "Destino": destino, "Contrato": contrato, "Documento": documento, 
            "Placa": placa, "Silo": silo, **respuestas, "Estatus": estatus
        }
        
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        df_nuevo = pd.DataFrame([registro])
        
        if os.path.exists(archivo_exc):
            pd.concat([pd.read_excel(archivo_exc), df_nuevo], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
        st.success(f"Guardado exitosamente como {estatus}")

# --- DESCARGAS ---
st.divider()
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
