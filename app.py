import streamlit as st
import pandas as pd
import plotly.express as px

from src.processamento import carregar_dados
from src.indicadores import calcular_indicadores
from src.surtos import detectar_surtos

st.set_page_config(page_title="Vigilância Epidemiológica", layout="wide")

st.title("📊 Sistema de Monitoramento Epidemiológico")

# Upload
arquivo = st.file_uploader("Envie o arquivo CSV", type=["csv"])

if arquivo:
    df = carregar_dados(arquivo)

    st.subheader("🔎 Dados")
    st.dataframe(df)

    # Indicadores
    populacao = st.number_input("População estimada", value=100000)

    total_casos, total_obitos, incidencia, letalidade = calcular_indicadores(df, populacao)

    col1, col2 = st.columns(2)
    col1.metric("Total de Casos", total_casos)
    col2.metric("Total de Óbitos", total_obitos)

    st.write(f"Incidência: {incidencia:.2f} por 100 mil hab")
    st.write(f"Letalidade: {letalidade:.2f}%")

    # Curva epidêmica
    st.subheader("📈 Curva Epidêmica")

    serie = df.groupby('data')['casos'].sum().reset_index()

    fig = px.line(serie, x='data', y='casos', title="Casos ao longo do tempo")
    st.plotly_chart(fig, use_container_width=True)

    # Bairro
    st.subheader("🗺️ Casos por bairro")

    bairro = df.groupby('bairro')['casos'].sum().reset_index()

    fig2 = px.bar(bairro, x='bairro', y='casos', title="Casos por bairro")
    st.plotly_chart(fig2, use_container_width=True)

    # Surtos
    st.subheader("🚨 Detecção de surtos")

    limite, surtos = detectar_surtos(serie)

    st.write(f"Limite de alerta: {limite:.2f}")

    if not surtos.empty:
        st.error("⚠️ POSSÍVEL SURTO DETECTADO")
        st.dataframe(surtos)
    else:
        st.success("Sem surtos detectados")

else:
    st.info("Envie um arquivo CSV para iniciar")
