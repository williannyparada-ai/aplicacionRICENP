import streamlit as st
import requests

# Leer la clave desde los secretos de Streamlit
OCR_API_KEY = st.secrets["OCR_API_KEY"]

def procesar_con_ocr(archivo):
    url = "https://api.ocr.space/parse/image"
    files = {"file": archivo.getvalue()}
    # Pasamos la clave como un diccionario
    payload = {"apikey": OCR_API_KEY, "language": "spa", "isOverlayRequired": False}
    
    try:
        response = requests.post(url, files=files, data=payload)
        result = response.json()
        
        if result.get("IsErroredOnProcessing"):
            st.error(f"Error técnico del OCR: {result.get('ErrorMessage')}")
            return None
        return result["ParsedResults"][0]["ParsedText"]
    except Exception as e:
        st.error(f"No se pudo conectar con el servidor OCR: {e}")
        return None
