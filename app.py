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
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {'items': {}}

st.title("🌾 Registro de Calidad - Provencesa")

# --- ESCÁNER ---
with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR"):
        with st.spinner("Extrayendo datos..."):
            try:
                prompt = 'Extrae los 20 datos en JSON plano: {"items": {"01": 0.0, ...}}. Solo JSON.'
                res = model.generate_content([prompt, Image.open(archivo)])
                texto_limpio = res.text.replace('```json', '').replace('```', '').strip()
                st.session_state.datos_ia = json.loads(texto_limpio)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- FORMULARIO DE REGISTRO ---
with st.form("registro_maestro"):
    items = st.session_state.datos_ia.get('items', {})
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            val = items.get(str(i+1).zfill(2), 0.0)
            try: valor = float(val)
            except: valor = 0.0
            respuestas[nombres[i]] = st.number_input(f"{i+1}. {nombres[i]}", value=valor)

    # Selección manual de estatus
    estatus = st.radio("Estatus:", ["Aprobado", "Rechazado"], horizontal=True)
    
    if st.form_submit_button("✅ REGISTRAR Y GUARDAR"):
        # Guardar en archivo según la elección del usuario
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        df_nuevo = pd.DataFrame([{**respuestas, "Fecha": str(datetime.now().date()), "Estatus": estatus}])
        
        if os.path.exists(archivo_exc):
            pd.concat([pd.read_excel(archivo_exc), df_nuevo], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
            
        st.success(f"Registro guardado exitosamente en **{archivo_exc}**")

# --- DESCARGAS ---
st.divider()
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
