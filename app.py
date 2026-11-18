import os
import sqlite3
import pandas as pd
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="centered")
st.title("Asistente Analista de Datos con IA")
st.write("Sube un archivo CSV o usa los datos de prueba y haz preguntas en lenguaje natural.")

api_key = st.sidebar.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password")

uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    st.info("Usando dataset de ventas de ejemplo.")
    df = pd.DataFrame({
        "producto": ["Laptop Pro", "Mouse Inalámbrico", "Monitor 4K", "Teclado Mecánico", "Laptop Pro"],
        "categoria": ["Computadoras", "Accesorios", "Monitores", "Accesorios", "Computadoras"],
        "precio": list((1200, 25, 450, 80, 1200)),
        "cantidad": list((3, 15, 4, 10, 2)),
        "ciudad": ["Panamá", "David", "Santiago", "Panamá", "Santiago"]
    })

st.dataframe(df.head(), use_container_width=True)

conn = sqlite3.connect(":memory:")
df.to_sql("datos", conn, index=False, if_exists="replace")

pregunta = st.text_input("¿Qué deseas saber sobre estos datos?",
                         placeholder="Ej: ¿Cuál es el total de ventas por ciudad?")

if st.button("Analizar") and pregunta:
    if not api_key:
        st.error("Por favor ingresa tu Groq API Key en la barra lateral.")
    else:
        client = Groq(api_key=api_key.strip())
        columnas = ", ".join([f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)])

        prompt_sql = f"""
        Eres un experto en SQLite. Dada la tabla 'datos' con las columnas: {columnas}.
        Genera ÚNICAMENTE la consulta SQL válida para responder: "{pregunta}".
        No incluyas explicaciones ni bloques markdown (```sql). Solo el código SQL puro.
        """

        with st.spinner("Generando consulta y analizando con Groq..."):
            resp_sql = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt_sql}],
                temperature=0
            )
            query = next(iter(resp_sql.choices)).message.content.strip()

            try:
                resultado_df = pd.read_sql_query(query, conn)
                st.subheader("Resultado:")
                st.dataframe(resultado_df, use_container_width=True)
                with st.expander("Ver consulta SQL generada"):
                    st.code(query, language="sql")
            except Exception as e:
                st.error(f"Error al ejecutar la consulta: {e}")
