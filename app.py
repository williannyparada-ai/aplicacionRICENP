import streamlit as st
import requests

st.title("Procesador de Calidad - OCR.space")

# Tu clave de OCR.space
API_KEY = "K83381284588957"

archivo = st.file_uploader("Sube la imagen", type=["jpg", "png"])

if archivo:
    if st.button("Procesar con OCR.space"):
        with st.spinner("Leyendo imagen..."):
            # Preparar la imagen para OCR.space
            payload = {
                'apikey': API_KEY,
                'language': 'spa',
                'isOverlayRequired': False,
            }
            files = {'file': archivo.getvalue()}
            
            # Llamada a la API de OCR.space
            response = requests.post('https://api.ocr.space/parse/image', 
                                     files=files, data=payload)
            
            resultado = response.json()
            
            # Verificar si funcionó
            if resultado.get("IsErroredOnProcessing") == False:
                texto_extraido = resultado["ParsedResults"][0]["ParsedText"]
                st.write("### Texto extraído:")
                st.text(texto_extraido)
            else:
                st.error(f"Error: {resultado.get('ErrorMessage')}")
