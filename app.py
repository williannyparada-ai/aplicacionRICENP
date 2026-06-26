import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import json
import pandas as pd
import os

st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN DE IA (SOLUCIÓN ROBUSTA) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # Intentamos conectar con el modelo estándar
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prueba de conexión rápida
    # Si esta línea falla, el bloque 'except' la atrapará
    model.generate_content("Hola") 
    
except Exception as e:
    st.error(f"Error de conexión con Gemini: {e}")
    st.warning("Intentando cambiar a 'gemini-1.0-pro'...")
    try:
        # Fallback al modelo anterior si el 1.5 falla
        model = genai.GenerativeModel('gemini-1.0-pro')
    except Exception as e2:
        st.error(f"Error crítico: No se pudo conectar a ningún modelo. Verifica tu API Key. Detalles: {e2}")
        model = None

# --- LÓGICA COVENIN ---
def determinar_clase(d):
    if d.get("Aflatoxina", 0) > 0: return "Rechazado"
    if (d.get("Total Dañados",0) <= 6 and d.get("Impureza",0) <= 2 and d.get("Granos Part.",0) <= 3 and 
        d.get("Dañado Calor",0) <= 1 and d.get("Cristalizados",0) <= 5 and d.get("Peso Vol",0) >= 0.760):
        return "Clase I"
    return "Clase II o III"

# --- ESTADO ---
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {'cabecera': {}, 'items': {}}

st.title("🌾 Registro de Información - Provencesa")

# 1. ENTRADA DE DATOS
col1, col2 = st.columns(2)
analista = col1.text_input("Nombre y Apellido del Analista")
fecha = col2.date_input("Fecha de Inspección")

# 2. ESCÁNER
with st.sidebar:
    st.header("📸 Escáner")
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR PLANILLA"):
        with st.spinner("IA trabajando..."):
            img = Image.open(archivo)
            prompt = "Extrae los 20 items de la tabla y la cabecera. Devuelve SOLO JSON con estructura: {'cabecera': {...}, 'items': {'01': val, ...}}"
            response = model.generate_content([prompt, img])
            try:
                st.session_state.datos_ia = json.loads(response.text.replace('```json','').replace('```',''))
                st.success("¡Datos cargados!")
                st.rerun()
            except: st.error("Error al procesar la IA")

# 3. FORMULARIO MAESTRO
with st.form("registro_maestro"):
    d = st.session_state.datos_ia
    cabe = d.get('cabecera', {})
    items = d.get('items', {})

    c1, c2, c3, c4 = st.columns(4)
    f_placa = c1.text_input("Placa", value=cabe.get('placa', ''))
    f_procedencia = c2.text_input("Procedencia", value=cabe.get('procedencia', ''))
    f_silo = c3.text_input("Silo", value=cabe.get('silo', ''))
    f_doc = c4.text_input("Documento", value=cabe.get('documento', ''))

    st.subheader("🔬 Resultados")
    nombres = ["Humedad", "Impureza", "Germen Dañado", "Dañado Calor", "Dañado Insecto", 
               "Infectados", "Total Dañados", "Partidos Peq.", "Granos Part.", "Total Part.",
               "Cristalizados", "Mezcla Color", "Peso Vol", "Color", "Olor", "Aflatoxina",
               "Insectos V.", "Quemados", "Sensorial", "Semillas Obj."]
    
    respuestas = {}
    cols = st.columns(4)
    for i in range(20):
        with cols[i%4]:
            key = str(i+1).zfill(2)
            val = items.get(key, 0.0)
            respuestas[nombres[i]] = st.number_input(f"{nombres[i]}", value=float(val))

    f_estatus = st.radio("Estatus:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de Rechazo (si aplica)")
    
    # EL BOTÓN DE ENVÍO DEBE ESTAR DENTRO DEL BLOQUE "with st.form"
    submit = st.form_submit_button("✅ REGISTRAR Y GUARDAR")

    if submit:
        clase = determinar_clase(respuestas)
        registro = {**respuestas, "Analista": analista, "Fecha": str(fecha), "Placa": f_placa, 
                    "Estatus": f_estatus, "Motivo": f_motivo, "Clase": clase}
        
        # Guardado en Excel
        archivo_exc = "aprobados.xlsx" if f_estatus == 'Aprobado' else "rechazados.xlsx"
        df_nuevo = pd.DataFrame([registro])
        if os.path.exists(archivo_exc):
            df_old = pd.read_excel(archivo_exc)
            df_new = pd.concat([df_old, df_nuevo], ignore_index=True)
            df_new.to_excel(archivo_exc, index=False)
        else:
            df_nuevo.to_excel(archivo_exc, index=False)
            
        st.success(f"Registrado como: **{clase}**")
