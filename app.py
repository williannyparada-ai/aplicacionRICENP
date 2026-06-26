import streamlit as st
import requests

st.title("Procesador de Calidad - OCR.space")

# Recuperar la API_KEY de los Secrets de Streamlit
try:
    API_KEY = st.secrets["OCR_API_KEY"]
except:
    API_KEY = "K83381284588957" # Fallback por si acaso

archivo = st.file_uploader("Sube la imagen", type=["jpg", "png", "jpeg"])

if archivo:
    if st.button("Procesar con OCR.space"):
        with st.spinner("Leyendo imagen..."):
            # Configuramos el envío con el nombre del archivo explícito
            payload = {
                'apikey': API_KEY,
                'language': 'spa',
                'isOverlayRequired': False,
            }
            
            # Ajuste clave: Pasamos el nombre del archivo junto con los bytes
            files = {'file': (archivo.name, archivo.getvalue())}
            
            try:
                response = requests.post('https://api.ocr.space/parse/image', 
                                         files=files, data=payload)
                resultado = response.json()
                
                if resultado.get("IsErroredOnProcessing") == False:
                    texto_extraido = resultado["ParsedResults"][0]["ParsedText"]
                    st.write("### Texto extraído:")
                    st.text(texto_extraido)
                else:
                    st.error(f"Error de la API: {resultado.get('ErrorMessage')}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
