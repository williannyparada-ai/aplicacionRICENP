import streamlit as st
import google.generativeai as genai
import json
from PIL import Image

# Configuración de la API
api_key = st.secrets["OCR_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash') # Asegúrate que este modelo esté activo

st.title("Procesador de Análisis")

archivo = st.file_uploader("Sube la imagen", type=["jpg", "png"])

if archivo:
    if st.button("Procesar con IA"):
        with st.spinner("IA trabajando..."):
            img = Image.open(archivo)
            prompt = """Extrae los datos de la tabla y la cabecera. 
            Responde EXCLUSIVAMENTE en formato JSON con esta estructura:
            {"cabecera": {"fecha": "", "lote": ""}, "items": []}"""
            
            try:
                response = model.generate_content([prompt, img])
                # Limpiamos el texto por si trae etiquetas de markdown
                texto_limpio = response.text.replace('```json', '').replace('```', '')
                st.session_state.datos_ia = json.loads(texto_limpio)
                st.success("¡Datos cargados correctamente!")
            except Exception as e:
                st.error(f"Error al procesar con IA: {e}")
                st.write("Respuesta cruda de la IA:", response.text if 'response' in locals() else "Sin respuesta")

# 3. FORMULARIO (Solo si los datos existen)
if 'datos_ia' in st.session_state and isinstance(st.session_state.datos_ia, dict):
    d = st.session_state.datos_ia
    cabe = d.get('cabecera', {})
    
    with st.form("registro_form"):
        st.write("### Cabecera")
        fecha = st.text_input("Fecha", value=cabe.get('fecha', ''))
        
        # Aquí irían tus inputs de los items
        if st.form_submit_button("✅ REGISTRAR"):
            st.write("Guardando...")
else:
    st.info("Sube una imagen para comenzar.")
