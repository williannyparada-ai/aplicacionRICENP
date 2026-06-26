import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import json
import pandas as pd
import os
import time

st.set_page_config(page_title="App Calidad Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') # Modelo optimizado para velocidad
except: model = None

if 'datos_ia' not in st.session_state: 
    st.session_state.datos_ia = {'cabecera': {}, 'items': {}}

st.title("🌾 Registro de Calidad - Provencesa")

# --- 2. BARRA LATERAL (PROCESAR Y LIMPIAR) ---
with st.sidebar:
    st.write("Modelo: gemini-1.5-flash")
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    
    if archivo and model and st.button("🤖 PROCESAR PLANILLA"):
        with st.spinner("Procesando con reintento automático..."):
            prompt = 'Extrae los 20 datos en JSON plano. Estructura: {"cabecera": {"Procedencia":"", "Destino":"", "Contrato":"", "Documento":"", "Placa":"", "Silo":""}, "items": {"01": 0.0, ...}}'
            
            # Lógica de Reintento (hasta 3 veces si hay error de cuota)
            for intento in range(3):
                try:
                    res = model.generate_content([prompt, Image.open(archivo)])
                    texto = res.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.datos_ia = json.loads(texto)
                    st.rerun()
                    break 
                except Exception as e:
                    if "429" in str(e) and intento < 2:
                        time.sleep(10) # Espera 10 segundos y reintenta
                    else:
                        st.error(f"Error tras reintentos: {e}")
                        break

    st.divider()
    if st.button("🧹 BORRAR TODO Y EMPEZAR DE CERO"):
        st.session_state.datos_ia = {'cabecera': {}, 'items': {}}
        for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
            if os.path.exists(ar): os.remove(ar)
        st.rerun()

# --- 3. FORMULARIO ---
with st.form("registro_maestro"):
    cab = st.session_state.datos_ia.get('cabecera', {})
    items = st.session_state.datos_ia.get('items', {})
    
    c1, c2, c3 = st.columns(3)
    analista = c1.text_input("Analista", "")
    fecha = c2.date_input("Fecha", datetime.now())
    procedencia = c3.text_input("Procedencia", cab.get("Procedencia", ""))
    
    c4, c5, c6 = st.columns(3)
    cereal = c4.selectbox("Cereal", ["", "Maíz Blanco", "Maíz Amarillo"], index=0)
    origen = c5.radio("Origen", ["Nacional", "Importado"], horizontal=True)
    destino = c6.text_input("Destino", cab.get("Destino", ""))
    
    c7, c8, c9, c10 = st.columns(4)
    contrato = c7.text_input("N Contrato", cab.get("Contrato", ""))
    documento = c8.text_input("Documento", cab.get("Documento", ""))
    placa = c9.text_input("Placa", cab.get("Placa", ""))
    silo = c10.text_input("Silo", cab.get("Silo", ""))

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
    
    orden_cols = ["Fecha", "Analista", "Estatus", "Procedencia", "Destino", "Cereal", "Origen", "Silo", "Contrato", "Placa", "Documento"] + nombres
    
    if st.form_submit_button("✅ REGISTRAR Y GUARDAR"):
        registro = {
            "Fecha": str(fecha), "Analista": analista, "Estatus": estatus, "Procedencia": procedencia,
            "Destino": destino, "Cereal": cereal, "Origen": origen, "Silo": silo, 
            "Contrato": contrato, "Placa": placa, "Documento": documento, **respuestas
        }
        
        archivo_exc = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        df_nuevo = pd.DataFrame([registro], columns=orden_cols)
        
        if os.path.exists(archivo_exc):
            df_existente = pd.read_excel(archivo_exc)
            pd.concat([df_existente, df_nuevo], ignore_index=True)[orden_cols].to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
        st.success(f"Guardado en {archivo_exc}")

# --- 4. DESCARGAS ---
st.divider()
for ar in ["aprobados.xlsx", "rechazados.xlsx"]:
    if os.path.exists(ar):
        with open(ar, "rb") as f:
            st.download_button(f"📥 Descargar {ar}", f, file_name=ar)
