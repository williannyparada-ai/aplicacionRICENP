import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import json

st.set_page_config(page_title="Sistema Provencesa", layout="wide", page_icon="🌾")

# --- 1. CONFIGURACIÓN IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Error en API KEY. Configúrala en los Secrets.")

# --- 2. ESTADO INICIAL ---
if 'datos_ia' not in st.session_state:
    st.session_state.datos_ia = {"Humedad": 0.0, "Total Dañados": 0.0, "Impureza": 0.0, "Total Part.": 0.0}
if 'aprobados' not in st.session_state: st.session_state.aprobados = pd.DataFrame()
if 'rechazados' not in st.session_state: st.session_state.rechazados = pd.DataFrame()

# --- 3. UI Y LÓGICA ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Nombre y Apellido")
    fecha_hoy = st.date_input("Fecha", datetime.now())

if not nombre_analista:
    st.warning("Ingresa tu nombre para comenzar.")
    st.stop()

st.title("🌾 Registro de Calidad")
archivo_foto = st.file_uploader("📸 Foto de planilla", type=['jpg', 'jpeg', 'png'])

if archivo_foto and st.button("🤖 Procesar con IA"):
    with st.spinner("Analizando..."):
        try:
            img = Image.open(archivo_foto)
            prompt = "Extrae: Humedad, Total Dañados, Impureza, Total Partidos. Responde solo JSON."
            response = model.generate_content([prompt, img])
            st.session_state.datos_ia = json.loads(response.text.replace('```json', '').replace('```', ''))
            st.success("¡Datos extraídos!")
        except Exception as e:
            st.error("Error al leer, ingresa manualmente.")

# --- 4. FORMULARIO CORRECTO ---
with st.form("registro_form"):
    placa = st.text_input("Placa del Vehículo")
    h = st.number_input("Humedad (%)", value=float(st.session_state.datos_ia.get("Humedad", 0.0)))
    d = st.number_input("Total Dañados (%)", value=float(st.session_state.datos_ia.get("Total Dañados", 0.0)))
    i = st.number_input("Impureza (%)", value=float(st.session_state.datos_ia.get("Impureza", 0.0)))
    p = st.number_input("Total Partidos (%)", value=float(st.session_state.datos_ia.get("Total Part.", 0.0)))
    estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"])
    motivo = st.text_input("Motivo de rechazo")
    
    # EL BOTÓN DEBE ESTAR DENTRO DEL FORM
    submit = st.form_submit_button("Registrar Vehículo")

if submit:
    # Lógica COVENIN (Simplificada)
    clase = "CLASE I" if d <= 6 and i <= 2 and p <= 3 else ("CLASE II" if d <= 8 and p <= 5 else "CLASE III")
    
    fila = pd.DataFrame([{"Fecha": str(fecha_hoy), "Analista": nombre_analista, "Placa": placa, 
                         "Humedad": h, "Total Dañados": d, "Impureza": i, "Clase": clase}])
    
    if estatus == "Aprobado":
        st.session_state.aprobados = pd.concat([st.session_state.aprobados, fila], ignore_index=True)
    else:
        fila["Motivo"] = motivo
        st.session_state.rechazados = pd.concat([st.session_state.rechazados, fila], ignore_index=True)
    st.success(f"Registrado como {clase}")

# --- 5. EXPORTACIÓN ---
c1, c2 = st.columns(2)
if not st.session_state.aprobados.empty:
    c1.subheader("✅ Aprobados"); c1.dataframe(st.session_state.aprobados)
    c1.download_button("Descargar Aprobados", st.session_state.aprobados.to_csv(index=False), "aprobados.csv")

if not st.session_state.rechazados.empty:
    c2.subheader("❌ Rechazados"); c2.dataframe(st.session_state.rechazados)
    c2.download_button("Descargar Rechazados", st.session_state.rechazados.to_csv(index=False), "rechazados.csv")
