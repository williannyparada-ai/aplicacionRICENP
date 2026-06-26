import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import json

# Configuración de página
st.set_page_config(page_title="Sistema Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # Buscamos un modelo que soporte generateContent automáticamente
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Priorizamos modelos 'flash' o 'pro' disponibles
    nombre_modelo = next((m for m in modelos if 'gemini-1.5-flash' in m), modelos[0])
    model = genai.GenerativeModel(nombre_modelo)
except Exception as e:
    st.error(f"Error crítico al conectar con la IA: {e}")
    st.stop()

# --- 2. LOGUEO (Barra Lateral) ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Nombre y Apellido")
    fecha_hoy = st.date_input("Fecha", datetime.now())

if not nombre_analista:
    st.warning("Por favor, ingresa tu nombre en la barra lateral para comenzar.")
    st.stop()

# --- 3. LÓGICA COVENIN ---
def clasificar_covenin(d):
    # Lógica según norma COVENIN 1935:2017
    if d["Total Dañados"] <= 6 and d["Impureza"] <= 2 and d["Total Part."] <= 3: 
        return "CLASE I"
    elif d["Total Dañados"] <= 8 and d["Impureza"] <= 2 and d["Total Part."] <= 5: 
        return "CLASE II"
    else: 
        return "CLASE III"

# --- 4. GESTIÓN DE SESIÓN ---
if 'aprobados' not in st.session_state: st.session_state.aprobados = pd.DataFrame()
if 'rechazados' not in st.session_state: st.session_state.rechazados = pd.DataFrame()

# --- 5. ESCÁNER Y FORMULARIO ---
st.title("🌾 Registro de Calidad Provencesa")
archivo_foto = st.file_uploader("📸 Tomar foto o subir planilla", type=['jpg', 'jpeg', 'png'])

datos_ia = {"Humedad": 0.0, "Total Dañados": 0.0, "Impureza": 0.0, "Total Part.": 0.0}

if archivo_foto:
    img = Image.open(archivo_foto)
    st.image(img, caption="Planilla capturada", use_container_width=True)
    if st.button("🤖 Procesar con IA"):
        with st.spinner("Analizando con Gemini..."):
            try:
                prompt = "Extrae de la imagen los datos: Humedad, Total Dañados, Impureza, Total Partidos. Devuelve SOLO un formato JSON puro."
                response = model.generate_content([prompt, img])
                texto_limpio = response.text.replace('```json', '').replace('```', '')
                datos_ia = json.loads(texto_limpio)
                st.success("¡Lectura exitosa!")
            except Exception as e:
                st.error(f"Error procesando imagen: {e}. Por favor, rellena los datos manualmente.")

with st.form("registro"):
    placa = st.text_input("Placa del Vehículo")
    h = st.number_input("Humedad (%)", value=float(datos_ia.get("Humedad", 0.0)))
    d = st.number_input("Total Dañados (%)", value=float(datos_ia.get("Total Dañados", 0.0)))
    i = st.number_input("Impureza (%)", value=float(datos_ia.get("Impureza", 0.0)))
    p = st.number_input("Total Partidos (%)", value=float(datos_ia.get("Total Part.", 0.0)))
    estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"])
    motivo = st.text_input("Motivo de rechazo (si aplica)")
    
    if st.form_submit_button("Registrar Vehículo"):
        clase = clasificar_covenin({"Total Dañados": d, "Impureza": i, "Total Part.": p})
        nueva_fila = pd.DataFrame([{
            "Fecha": str(fecha_hoy), "Analista": nombre_analista, "Placa": placa, 
            "Humedad": h, "Total Dañados": d, "Impureza": i, "Clase": clase
        }])
        
        if estatus == "Aprobado":
            st.session_state.aprobados = pd.concat([st.session_state.aprobados, nueva_fila], ignore_index=True)
            st.success(f"Registrado como {clase}")
        else:
            nueva_fila["Motivo"] = motivo
            st.session_state.rechazados = pd.concat([st.session_state.rechazados, nueva_fila], ignore_index=True)
            st.error("Vehículo Rechazado registrado")

# --- 6. DESCARGAS ---
st.divider()
c1, c2 = st.columns(2)
if not st.session_state.aprobados.empty:
    c1.subheader("✅ Mis Aprobados")
    c1.dataframe(st.session_state.aprobados)
    csv = st.session_state.aprobados.to_csv(index=False).encode('utf-8')
    c1.download_button("Descargar Excel Aprobados", csv, "aprobados.csv", "text/csv")

if not st.session_state.rechazados.empty:
    c2.subheader("❌ Mis Rechazados")
    c2.dataframe(st.session_state.rechazados)
    csv_r = st.session_state.rechazados.to_csv(index=False).encode('utf-8')
    c2.download_button("Descargar Excel Rechazados", csv_r, "rechazados.csv", "text/csv")
