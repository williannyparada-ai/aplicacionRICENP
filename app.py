import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="App Provencesa", layout="wide")

# Configuración IA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except: model = None

# --- LÓGICA COVENIN 1935:2017 ---
def clasificar_maiz(datos):
    # Nota: Asumimos 'Maíz Acondicionado' basado en la tabla
    if datos["Total Dañados"] <= 6 and datos["Impureza"] <= 2 and datos["Granos Part."] <= 3 and datos["Peso Vol"] >= 0.760:
        return "Clase I"
    elif datos["Total Dañados"] <= 8 and datos["Impureza"] <= 2 and datos["Granos Part."] <= 5 and datos["Peso Vol"] >= 0.745:
        return "Clase II"
    elif datos["Total Dañados"] <= 11 and datos["Impureza"] <= 2 and datos["Granos Part."] <= 7 and datos["Peso Vol"] >= 0.730:
        return "Clase III"
    else:
        return "Rechazado"

# --- INTERFAZ ---
st.title("🌾 Registro de Calidad Provencesa")

# Registro del Analista
col1, col2 = st.columns(2)
analista = col1.text_input("Nombre del Analista")
fecha = col2.date_input("Fecha", datetime.now())

# Formulario
with st.form("registro"):
    # ... (Tus campos de placa, silo, etc.) ...
    
    # Ejemplo de cómo capturar campos para la tabla
    humedad = st.number_input("Humedad (%)", min_value=0.0, max_value=30.0)
    impureza = st.number_input("Impurezas (%)", min_value=0.0, max_value=10.0)
    total_danados = st.number_input("Total Dañados (%)")
    granos_part = st.number_input("Granos Partidos (%)")
    peso_vol = st.number_input("Peso Volumétrico (kg/L)")
    
    estatus = st.radio("Estatus", ["Aprobado", "Rechazado"])
    motivo_rechazo = st.text_input("Motivo de Rechazo (si aplica)")
    
    submitted = st.form_submit_button("REGISTRAR")

    if submitted:
        datos_analisis = {
            "Total Dañados": total_danados, "Impureza": impureza, 
            "Granos Part.": granos_part, "Peso Vol": peso_vol
        }
        clase = clasificar_maiz(datos_analisis)
        
        # Guardar en Excel
        archivo = "aprobados.xlsx" if estatus == "Aprobado" else "rechazados.xlsx"
        df_nuevo = pd.DataFrame([{**datos_analisis, "Clase": clase, "Analista": analista, "Fecha": fecha}])
        
        if os.path.exists(archivo):
            df_existente = pd.read_excel(archivo)
            df_nuevo = pd.concat([df_existente, df_nuevo], ignore_index=True)
        
        df_nuevo.to_excel(archivo, index=False)
        st.success(f"Registrado como {clase}")

# --- REPORTE DIARIO ---
if os.path.exists("aprobados.xlsx"):
    df_aprobados = pd.read_excel("aprobados.xlsx")
    st.subheader("📈 Reporte Diario")
    st.metric("Promedio Humedad", f"{df_aprobados['Humedad'].mean():.2f}%")
