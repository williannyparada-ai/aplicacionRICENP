import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import json
import io
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Registro Provencesa", layout="wide", page_icon="🌾")

# Configuración de IA (Manteniendo tu estructura)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Error: Configura la GOOGLE_API_KEY en los secretos.")

# --- LÓGICA DE CLASIFICACIÓN COVENIN ---
def obtener_clase(d):
    # Lógica basada en la tabla COVENIN 1935:2017
    # Se asume maíz acondicionado para límites más estrictos
    if (d["Total Dañados"] <= 6 and d["Impureza"] <= 2 and d["Granos Part."] <= 3 and 
        d["Dañado Calor"] <= 1 and d["Cristalizados"] <= 5 and d["Peso Vol"] >= 0.760):
        return "I"
    elif (d["Total Dañados"] <= 8 and d["Impureza"] <= 2 and d["Granos Part."] <= 5 and 
          d["Dañado Calor"] <= 2 and d["Cristalizados"] <= 10 and d["Peso Vol"] >= 0.745):
        return "II"
    elif (d["Total Dañados"] <= 11 and d["Impureza"] <= 2 and d["Granos Part."] <= 7 and 
          d["Dañado Calor"] <= 3 and d["Cristalizados"] <= 15 and d["Peso Vol"] >= 0.730):
        return "III"
    else:
        return "Fuera de Norma"

# --- PERSISTENCIA EXCEL ---
def guardar_en_excel(datos, estatus):
    archivo = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
    df_nuevo = pd.DataFrame([datos])
    if os.path.exists(archivo):
        df_existente = pd.read_excel(archivo)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo
    df_final.to_excel(archivo, index=False)

# --- ESTADO INICIAL ---
if 'datos_ia' not in st.session_state: st.session_state.datos_ia = {}

st.title("🌾 Registro de Información Provencesa")

# Entrada de Analista y Fecha
c1, c2 = st.columns(2)
analista = c1.text_input("Nombre y Apellido del Analista")
fecha_reg = c2.date_input("Fecha de Registro")

# --- SIDEBAR (ESCÁNER) ---
with st.sidebar:
    st.header("📸 Escáner de Planilla")
    archivo = st.file_uploader("Subir foto", type=['jpg', 'jpeg', 'png'])
    if archivo and st.button("🤖 PROCESAR"):
        img = Image.open(archivo)
        with st.spinner("IA Analizando..."):
            # Aquí va tu lógica de IA para obtener el JSON
            # (Simplificado para el ejemplo)
            st.session_state.datos_ia = {"items": {"01": 12.0, "02": 1.5, "04": 0.5, "07": 4.0, "09": 2.0, "11": 4.0, "13": 0.770}} 
            st.success("¡Lectura exitosa!")

# --- FORMULARIO ---
d = st.session_state.datos_ia.get('items', {})
with st.form("registro_maestro"):
    st.subheader("🔬 Datos del Análisis")
    c1, c2, c3, c4 = st.columns(4)
    f_placa = c1.text_input("Placa")
    f_humedad = c2.number_input("Humedad", value=float(d.get("01", 0.0)))
    f_impureza = c3.number_input("Impureza", value=float(d.get("02", 0.0)))
    f_dañados = c4.number_input("Total Dañados", value=float(d.get("07", 0.0)))
    
    c5, c6, c7, c8 = st.columns(4)
    f_calor = c5.number_input("Dañado Calor", value=float(d.get("04", 0.0)))
    f_partidos = c6.number_input("Granos Part.", value=float(d.get("09", 0.0)))
    f_cristal = c7.number_input("Cristalizados", value=float(d.get("11", 0.0)))
    f_peso = c8.number_input("Peso Vol", value=float(d.get("13", 0.0)))

    clase_auto = obtener_clase({"Total Dañados": f_dañados, "Impureza": f_impureza, "Granos Part.": f_partidos, 
                                "Dañado Calor": f_calor, "Cristalizados": f_cristal, "Peso Vol": f_peso})
    
    st.info(f"Clasificación COVENIN sugerida: **{clase_auto}**")

    st.subheader("📢 Decisión Final")
    f_estatus = st.radio("Estatus", ["Aprobado", "Rechazado"], horizontal=True)
    f_motivo = st.text_input("Motivo de Rechazo (si aplica)")

    if st.form_submit_button("✅ REGISTRAR VEHÍCULO"):
        registro = {
            "Fecha": str(fecha_reg), "Analista": analista, "Placa": f_placa,
            "Humedad": f_humedad, "Clase": clase_auto, "Estatus": f_estatus, "Motivo": f_motivo
        }
        guardar_en_excel(registro, f_estatus)
        st.success(f"Registro guardado exitosamente como {f_estatus}")

# --- REPORTE DIARIO ---
if os.path.exists("aprobados.xlsx"):
    df = pd.read_excel("aprobados.xlsx")
    st.subheader("📊 Reporte Diario")
    st.metric("Promedio Humedad (Aprobados)", f"{df['Humedad'].mean():.2f}%")
