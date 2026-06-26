import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# --- CONFIGURACIÓN DE IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Detección automática de modelo para evitar error NotFound
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    nombre_modelo = next((m for m in modelos if 'gemini-1.5-flash' in m), modelos[0])
    model = genai.GenerativeModel(nombre_modelo)
except Exception as e:
    st.error(f"Error de configuración de IA: {e}")
    model = None

# --- LÓGICA COVENIN 1935:2017 ---
def determinar_clase(d):
    # Regla: Si es Aflatoxina, es rechazo
    if d.get("Aflatoxina", 0) > 0: return "Rechazado"
    
    # Evaluación por rangos (Maíz Acondicionado)
    if (d["Total Dañados"] <= 6 and d["Impureza"] <= 2 and d["Granos Part."] <= 3 and 
        d["Dañado Calor"] <= 1 and d["Cristalizados"] <= 5 and d["Peso Vol"] >= 0.760):
        return "Clase I"
    elif (d["Total Dañados"] <= 8 and d["Impureza"] <= 2 and d["Granos Part."] <= 5 and 
          d["Dañado Calor"] <= 2 and d["Cristalizados"] <= 10 and d["Peso Vol"] >= 0.745):
        return "Clase II"
    elif (d["Total Dañados"] <= 11 and d["Impureza"] <= 2 and d["Granos Part."] <= 7 and 
          d["Dañado Calor"] <= 3 and d["Cristalizados"] <= 15 and d["Peso Vol"] >= 0.730):
        return "Clase III"
    return "Rechazado"

# --- GESTIÓN DE DATOS ---
def guardar_en_excel(datos):
    archivo = "aprobados.xlsx" if datos['Estatus'] == 'Aprobado' else "rechazados.xlsx"
    df_nuevo = pd.DataFrame([datos])
    if os.path.exists(archivo):
        df = pd.read_excel(archivo)
        df = pd.concat([df, df_nuevo], ignore_index=True)
    else:
        df = df_nuevo
    df.to_excel(archivo, index=False)

# --- ESTADO ---
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

st.title("🌾 Registro de Información - Provencesa")

# 1. ENTRADA DE DATOS
c1, c2 = st.columns(2)
analista = c1.text_input("Nombre y Apellido del Analista")
fecha = c2.date_input("Fecha de Inspección")

# 2. ESCÁNER (SIDEBAR)
with st.sidebar:
    st.header("📸 Escáner")
    archivo = st.file_uploader("Subir planilla", type=['jpg', 'jpeg', 'png'])
    if archivo and model and st.button("🤖 PROCESAR PLANILLA"):
        img = Image.open(archivo)
        with st.spinner("IA trabajando..."):
            prompt = "Extrae los 20 items de la tabla y la cabecera. Devuelve SOLO JSON."
            response = model.generate_content([prompt, img])
            st.session_state.datos_ia = json.loads(response.text.replace('```json','').replace('```',''))
            st.success("¡Datos cargados!")

# 3. FORMULARIO
d = st.session_state.datos_ia
cabe = d.get('cabecera', {})
items = d.get('items', {})

with st.form("registro_maestro"):
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
            val = items.get(str(i+1).zfill(2), 0.0)
            respuestas[nombres[i]] = st.number_input(f"{nombres[i]}", value=float(val))

    f_estatus = st.radio("Estatus:", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de Rechazo (si aplica)")

    if st.form_submit_button("✅ REGISTRAR"):
        clase = determinar_clase(respuestas)
        registro = {**respuestas, "Analista": analista, "Fecha": str(fecha), "Placa": f_placa, 
                    "Estatus": f_estatus, "Motivo": f_motivo, "Clase": clase}
        
        guardar_en_excel(registro)
        st.success(f"Registrado. Clasificación COVENIN: **{clase}**")

# 4. REPORTE
if os.path.exists("aprobados.xlsx"):
    st.divider()
    st.subheader("📊 Resumen Diario")
    df_ap = pd.read_excel("aprobados.xlsx")
    st.metric("Promedio Humedad Aprobados", f"{df_ap['Humedad'].mean():.2f}%")
    st.dataframe(df_ap)
