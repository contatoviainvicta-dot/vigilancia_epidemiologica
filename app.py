import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Garantir path correto (evita erro no Streamlit Cloud)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

st.set_page_config(page_title="Vigilância - Trânsito", layout="wide")

st.title("🚗 Monitoramento Epidemiológico de Mortes no Trânsito")

st.markdown("""
Sistema para análise de mortalidade por acidentes de trânsito e associação com álcool e drogas.
Fonte recomendada: SIM/DATASUS (TABNET)
""")

# Upload
arquivo = st.file_uploader("Envie o CSV (SIM/TABNET ou estruturado)", type=["csv"])

# Tipo de dado
tipo = st.selectbox("Tipo de base", ["Estruturado", "TABNET"])

# -----------------------------
# FUNÇÕES
# -----------------------------

def tratar_tabnet(arquivo):
    df = pd.read_csv(arquivo, sep=';', encoding='latin-1')
    df = df.dropna(axis=1, how='all')
    df = df[~df.iloc[:,0].astype(str).str.contains("Total", case=False)]
    df = df.rename(columns={df.columns[0]: "categoria"})

    df = df.melt(
        id_vars="categoria",
        var_name="variavel",
        value_name="valor"
    )

    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    return df.dropna()

def carregar_estruturado(arquivo):
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='latin-1')
    except:
        df = pd.read_csv(arquivo, sep=',', encoding='utf-8')
    return df

def filtrar_transito(df):
    return df[df['cid'].str.startswith('V', na=False)]

def marcar_alcool_drogas(df):
    df['alcool'] = df['causa_associada'].str.contains('F10', na=False)
    df['drogas'] = df['causa_associada'].str.contains('F1', na=False)
    df['alcool_ou_drogas'] = df['alcool'] | df['drogas']
    return df

def calcular_metricas(df):
    total = len(df)
    alcool = df['alcool'].sum()
    drogas = df['drogas'].sum()
    ambos = df['alcool_ou_drogas'].sum()

    prop = (ambos / total) * 100 if total > 0 else 0

    return total, alcool, drogas, ambos, prop

# -----------------------------
# PROCESSAMENTO
# -----------------------------

if arquivo:

    if tipo == "TABNET":
        st.warning("Modo TABNET: análise limitada a tabelas agregadas")
        df = tratar_tabnet(arquivo)
        st.dataframe(df)

    else:
        df = carregar_estruturado(arquivo)

        st.subheader("🔎 Dados carregados")
        st.dataframe(df.head())

        # Verificação mínima
        colunas_necessarias = ['cid', 'causa_associada']
        if not all(col in df.columns for col in colunas_necessarias):
            st.error("O CSV precisa conter colunas: cid e causa_associada")
            st.stop()

        # Filtrar trânsito
        df_transito = filtrar_transito(df)

        # Marcar álcool/drogas
        df_transito = marcar_alcool_drogas(df_transito)

        # Métricas
        total, alcool, drogas, ambos, prop = calcular_metricas(df_transito)

        st.subheader("📊 Indicadores principais")

        col1, col2, col3 = st.columns(3)
        col1.metric("Óbitos por trânsito", total)
        col2.metric("Álcool associado", alcool)
        col3.metric("Drogas associadas", drogas)

        st.metric("Álcool ou drogas (%)", f"{prop:.2f}%")

        # -----------------------------
        # GRÁFICOS
        # -----------------------------

        st.subheader("📈 Distribuição das associações")

        resumo = pd.DataFrame({
            'Categoria': ['Álcool', 'Drogas', 'Álcool ou drogas'],
            'Casos': [alcool, drogas, ambos]
        })

        fig = px.bar(resumo, x='Categoria', y='Casos', title="Associação com substâncias")
        st.plotly_chart(fig, use_container_width=True)

        # Série temporal (se existir data)
        if 'data' in df_transito.columns:
            st.subheader("📅 Curva temporal")

            df_transito['data'] = pd.to_datetime(df_transito['data'], errors='coerce')
            serie = df_transito.groupby('data').size().reset_index(name='casos')

            fig2 = px.line(serie, x='data', y='casos', title="Óbitos ao longo do tempo")
            st.plotly_chart(fig2, use_container_width=True)

        # -----------------------------
        # NOTA EPIDEMIOLÓGICA AUTOMÁTICA
        # -----------------------------

        st.subheader("🧾 Nota Epidemiológica")

        if st.button("Gerar Nota"):
            texto = f"""
NOTA EPIDEMIOLÓGICA

Foram identificados {total} óbitos por acidentes de transporte terrestre (CID-10 V01–V99) no período analisado.

Dentre estes:
- {alcool} ({(alcool/total*100 if total>0 else 0):.2f}%) apresentaram associação com álcool (F10)
- {drogas} ({(drogas/total*100 if total>0 else 0):.2f}%) com outras drogas (F11–F19)
- {ambos} ({prop:.2f}%) com álcool ou drogas

Os achados sugerem relevante participação de substâncias psicoativas na mortalidade por trânsito.

LIMITAÇÕES:
- Subnotificação de álcool e drogas no SIM
- Possível ausência de exames toxicológicos

IMPLICAÇÕES:
- Reforço de políticas de fiscalização (Lei Seca)
- Estratégias de prevenção ao uso de substâncias ao volante
"""
            st.text_area("Texto gerado", texto, height=300)

else:
    st.info("Envie um arquivo CSV para iniciar a análise")
