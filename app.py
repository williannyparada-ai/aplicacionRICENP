import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuración de página
st.set_page_config(page_title="Sistema Provencesa", layout="wide")

st.title("🌾 Registro de Calidad Provencesa")

# --- 1. LOGIN / IDENTIFICACIÓN ---
with st.sidebar:
    st.header("👤 Identificación")
    nombre_analista = st.text_input("Nombre y Apellido")
    fecha_hoy = st.date_input("Fecha", datetime.now())
    st.info("Cada registro que realices se guardará en tu sesión local.")

if not nombre_analista:
    st.warning("Por favor, ingresa tu nombre en la barra lateral para comenzar.")
    st.stop()

# --- 2. LÓGICA COVENIN (Clasificación Automática) ---
def clasificar_covenin(datos):
    # Lógica basada en la tabla COVENIN 1935:2017
    # Nota: Simplificado para el ejemplo, ajusta según necesidad
    danados = datos.get("Total Dañados", 0)
    impurezas = datos.get("Impureza", 0)
    partidos = datos.get("Total Part.", 0)
    
    if danados <= 6 and impurezas <= 2 and partidos <= 3:
        return "CLASE I"
    elif danados <= 8 and impurezas <= 2 and partidos <= 5:
        return "CLASE II"
    else:
        return "CLASE III"

# --- 3. GESTIÓN DE ESTADO ---
if 'aprobados' not in st.session_state: st.session_state.aprobados = pd.DataFrame()
if 'rechazados' not in st.session_state: st.session_state.rechazados = pd.DataFrame()

# --- 4. FORMULARIO ---
with st.form("registro"):
    placa = st.text_input("Placa del Vehículo")
    humedad = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0)
    danados = st.number_input("Total Dañados (%)", min_value=0.0)
    impureza = st.number_input("Impureza (%)", min_value=0.0)
    partidos = st.number_input("Total Partidos (%)", min_value=0.0)
    
    estatus = st.radio("Decisión:", ["Aprobado", "Rechazado"])
    motivo = st.text_input("Motivo de rechazo (si aplica)")
    
    if st.form_submit_button("Registrar"):
        datos_fila = {
            "Fecha": fecha_hoy, "Analista": nombre_analista, "Placa": placa,
            "Humedad": humedad, "Total Dañados": danados, "Impureza": impureza, 
            "Total Part.": partidos, "Clase": clasificar_covenin({"Total Dañados": danados, "Impureza": impureza, "Total Part.": partidos})
        }
        
        if estatus == "Aprobado":
            st.session_state.aprobados = pd.concat([st.session_state.aprobados, pd.DataFrame([datos_fila])], ignore_index=True)
            st.success(f"Registrado como {datos_fila['Clase']}")
        else:
            datos_fila["Motivo"] = motivo
            st.session_state.rechazados = pd.concat([st.session_state.rechazados, pd.DataFrame([datos_fila])], ignore_index=True)
            st.error("Vehículo Rechazado")

# --- 5. EXPORTACIÓN INDEPENDIENTE ---
st.divider()
c1, c2 = st.columns(2)

if not st.session_state.aprobados.empty:
    c1.subheader("✅ Mis Aprobados")
    c1.dataframe(st.session_state.aprobados)
    # Cálculo promedio día
    promedio = st.session_state.aprobados['Humedad'].mean()
    c1.write(f"**Promedio Humedad del día: {promedio:.2f}%**")
    
    csv_apr = st.session_state.aprobados.to_csv(index=False).encode('utf-8')
    c1.download_button("Descargar Aprobados Excel", csv_apr, "aprobados.csv", "text/csv")

if not st.session_state.rechazados.empty:
    c2.subheader("❌ Mis Rechazados")
    c2.dataframe(st.session_state.rechazados)
    csv_rec = st.session_state.rechazados.to_csv(index=False).encode('utf-8')
    c2.download_button("Descargar Rechazados Excel", csv_rec, "rechazados.csv", "text/csv")