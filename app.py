import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import io
import json

# Configuración inicial
st.set_page_config(page_title="Registro de Calidad Provencesa", layout="wide", page_icon="🌾")

# --- LÓGICA COVENIN 1935:2017 ---
def determinar_clase_covenin(d):
    if d.get("Aflatoxina", 0) > 0: return "Rechazado"
    
    # Límites según tabla
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

# --- GESTIÓN DE ARCHIVOS ---
def guardar_registro(data):
    archivo = "aprobados.xlsx" if data['Estatus'] == 'Aprobado' else "rechazados.xlsx"
    df_nuevo = pd.DataFrame([data])
    if os.path.exists(archivo):
        df_existente = pd.read_excel(archivo)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo
    df_final.to_excel(archivo, index=False)

# --- INTERFAZ ---
st.title("🌾 Registro de Calidad Provencesa")

# Entrada de Analista
analista = st.text_input("Nombre y Apellido del Analista")

with st.form("registro_maestro"):
    c1, c2, c3 = st.columns(3)
    placa = c1.text_input("Placa del vehículo")
    cereal = c2.text_input("Cereal")
    estatus = c3.radio("Estatus:", ["Aprobado", "Rechazado"], horizontal=True)
    
    motivo = st.text_input("Motivo de rechazo (si aplica):")
    
    # Parámetros técnicos
    st.subheader("Datos de laboratorio")
    col1, col2, col3 = st.columns(3)
    humedad = col1.number_input("Humedad (%)", 0.0, 30.0)
    impureza = col2.number_input("Impureza (%)", 0.0, 20.0)
    dañados_totales = col3.number_input("Total Dañados (%)", 0.0, 20.0)
    
    col4, col5, col6 = st.columns(3)
    partidos = col4.number_input("Granos Partidos (%)", 0.0, 20.0)
    calor = col5.number_input("Dañado Calor (%)", 0.0, 10.0)
    cristal = col6.number_input("Cristalizados (%)", 0.0, 20.0)
    peso_vol = st.number_input("Peso Volumétrico (kg/L)", 0.0, 1.0, step=0.001)

    if st.form_submit_button("✅ REGISTRAR"):
        # Preparar datos
        data_analisis = {
            "Total Dañados": dañados_totales, "Impureza": impureza, 
            "Granos Part.": partidos, "Dañado Calor": calor, 
            "Cristalizados": cristal, "Peso Vol": peso_vol
        }
        
        clase = determinar_clase_covenin(data_analisis)
        
        registro = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Analista": analista, "Placa": placa, "Clase": clase,
            "Estatus": estatus, "Humedad": humedad, "Motivo": motivo
        }
        
        guardar_registro(registro)
        st.success(f"Registrado. Clasificación automática: {clase}")

# --- REPORTE DIARIO ---
if os.path.exists("aprobados.xlsx"):
    df_aprobados = pd.read_excel("aprobados.xlsx")
    st.subheader("📊 Reporte de Aprobados")
    st.metric("Promedio Humedad Aprobados", f"{df_aprobados['Humedad'].mean():.2f}%")
    st.dataframe(df_aprobados)
