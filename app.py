import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import json
import pandas as pd
import os

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN IA ROBUSTA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos un modelo más estándar y ampliamente disponible
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración IA: {e}")
    model = None

# --- LÓGICA COVENIN ---
def obtener_clase_covenin(d):
    if d.get("Aflatoxina", 0) > 0: return "Rechazado"
    if (d.get("Total Dañados",0) <= 6 and d.get("Impureza",0) <= 2 and d.get("Granos Part.",0) <= 3 and 
        d.get("Dañado Calor",0) <= 1 and d.get("Cristalizados",0) <= 5 and d.get("Peso Vol",0) >= 0.760):
        return "Clase I"
    elif (d.get("Total Dañados",0) <= 8 and d.get("Impureza",0) <= 2 and d.get("Granos Part.",0) <= 5 and 
          d.get("Dañado Calor",0) <= 2 and d.get("Cristalizados",0) <= 10 and d.get("Peso Vol",0) >= 0.745):
        return "Clase II"
    elif (d.get("Total Dañados",0) <= 11 and d.get("Impureza",0) <= 2 and d.get("Granos Part.",0) <= 7 and 
          d.get("Dañado Calor",0) <= 3 and d.get("Cristalizados",0) <= 15 and d.get("Peso Vol",0) >= 0.730):
        return "Clase III"
    return "Rechazado"

# --- INTERFAZ ---
st.title("🌾 Registro de Calidad - Provencesa")

if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {'items': {}}

with st.sidebar:
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR"):
        with st.spinner("Leyendo planilla..."):
            try:
                prompt = """Extrae los 20 datos y devuelve SOLO un JSON plano sin explicaciones.
                Estructura exacta: {"items": {"01": 0.0, "02": 0.0, ...}}"""
                res = model.generate_content([prompt, Image.open(archivo)])
                # Limpieza mejorada de respuesta
                texto = res.text.replace('```json', '').replace('```', '').strip()
                st.session_state.datos_ia = json.loads(texto)
                st.rerun()
            except Exception as e: 
                st.error(f"Error de lectura: {e}")
                st.write("Respuesta cruda de la IA:", res.text if 'res' in locals() else "Sin respuesta")

# --- FORMULARIO ---
with st.form("registro_maestro"):
    items = st.session_state.datos_ia.get('items', {})
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.", "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina", "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            val = items.get(str(i+1).zfill(2), 0.0)
            respuestas[nombres[i]] = st.number_input(f"{i+1}. {nombres[i]}", value=float(val))

    if st.form_submit_button("✅ REGISTRAR"):
        clase_automatica = obtener_clase_covenin(respuestas)
        respuestas["Sensorial"] = clase_automatica
        
        # Guardado seguro
        df_nuevo = pd.DataFrame([respuestas])
        archivo_exc = "aprobados.xlsx" if clase_automatica != "Rechazado" else "rechazados.xlsx"
        
        if os.path.exists(archivo_exc):
            pd.concat([pd.read_excel(archivo_exc), df_nuevo], ignore_index=True).to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
        st.success(f"Guardado. Clasificación: **{clase_automatica}**")

# --- DESCARGA ---
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
