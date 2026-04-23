import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Vigilância - Trânsito", layout="wide")

st.title("🚗 Monitoramento de Mortalidade por Acidentes de Trânsito")
st.markdown("Dados do SIM/DATASUS (TABNET ou estruturados)")

# -----------------------------
# UPLOAD
# -----------------------------
arquivo = st.file_uploader("Envie o arquivo (CSV ou Excel)", type=["csv", "xlsx"])

if arquivo is None:
    st.info("Aguardando upload do arquivo...")
    st.stop()

conteudo_bytes = arquivo.getvalue()

# -----------------------------
# FUNÇÃO DE LEITURA ROBUSTA
# -----------------------------
def carregar_dados(conteudo_bytes):

    # 1. Tentar Excel
    try:
        df = pd.read_excel(io.BytesIO(conteudo_bytes))
        if df.shape[1] > 1:
            return df
    except:
        pass

    # 2. Decodificar texto
    for enc in ['latin-1', 'utf-8', 'cp1252']:
        try:
            texto = conteudo_bytes.decode(enc)
            break
        except:
            continue
    else:
        raise Exception("Erro ao decodificar arquivo")

    linhas = texto.splitlines()

    # 3. Detectar início da tabela
    inicio_dados = None
    for i, linha in enumerate(linhas):
        if linha.count(';') >= 1:
            partes = linha.split(';')
            if len(partes) >= 2:
                inicio_dados = i
                break

    if inicio_dados is None:
        raise Exception("Tabela não encontrada no arquivo")

    dados_limpos = "\n".join(linhas[inicio_dados:])

    # 4. Ler CSV
    df = pd.read_csv(io.StringIO(dados_limpos), sep=';')

    return df


# -----------------------------
# TRANSFORMAR TABNET (WIDE → LONG)
# -----------------------------
def transformar_tabnet(df):
    df = df.copy()

    # Remover linha "Total"
    df = df[~df.iloc[:, 0].astype(str).str.contains("Total", case=False)]

    # Renomear primeira coluna
    df = df.rename(columns={df.columns[0]: "categoria"})

    # Converter formato
    df_long = df.melt(
        id_vars="categoria",
        var_name="ano",
        value_name="obitos"
    )

    # Limpar dados
    df_long['obitos'] = pd.to_numeric(df_long['obitos'], errors='coerce')

    return df_long.dropna()


# -----------------------------
# CARREGAR DADOS
# -----------------------------
try:
    df = carregar_dados(conteudo_bytes)
except Exception as e:
    st.error(f"Erro ao carregar arquivo: {e}")
    st.stop()

# -----------------------------
# DETECTAR TABNET
# -----------------------------
if df.shape[1] > 3:
    st.info("Formato TABNET detectado — reorganizando dados...")
    df = transformar_tabnet(df)

# -----------------------------
# VISÃO INICIAL
# -----------------------------
st.subheader("🔎 Dados")
st.write("Shape:", df.shape)
st.write("Colunas:", df.columns.tolist())
st.dataframe(df.head())

# -----------------------------
# DEFINIR COLUNAS
# -----------------------------
if "obitos" in df.columns:
    x_col = "categoria"
    y_col = "obitos"
else:
    colunas = df.columns.tolist()
    if len(colunas) < 2:
        st.error("Dados insuficientes para análise")
        st.stop()
    x_col = colunas[0]
    y_col = colunas[1]

# Converter valores
df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

# -----------------------------
# FILTRO
# -----------------------------
st.subheader("🔍 Filtro")

filtro = st.text_input("Filtrar categoria (ex: município ou mês)")

df_filtrado = df[df[x_col].astype(str).str.contains(filtro, case=False, na=False)]

# -----------------------------
# INDICADORES
# -----------------------------
st.subheader("📊 Indicadores")

populacao = st.number_input("População estimada", value=3000000)

total = df_filtrado[y_col].sum()
media = df_filtrado[y_col].mean()
taxa = (total / populacao) * 100000 if populacao > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de óbitos", int(total))
col2.metric("Média", round(media, 2))
col3.metric("Taxa por 100 mil", f"{taxa:.2f}")

# -----------------------------
# PROPORÇÃO
# -----------------------------
df_filtrado["proporcao"] = df_filtrado[y_col] / total * 100

# -----------------------------
# TOP 10
# -----------------------------
st.subheader("🔝 Top 10")

if "categoria" in df.columns:
    top10 = (
        df_filtrado.groupby("categoria")["obitos"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top10)
else:
    top10 = df_filtrado.sort_values(by=y_col, ascending=False).head(10)
    st.dataframe(top10)

# -----------------------------
# ALERTA
# -----------------------------
limite = df_filtrado[y_col].mean() + 2 * df_filtrado[y_col].std()

if df_filtrado[y_col].max() > limite:
    st.error("⚠️ Possível concentração elevada detectada")

# -----------------------------
# GRÁFICO
# -----------------------------
st.subheader("📊 Distribuição")

fig = px.bar(
    df_filtrado.sort_values(by=y_col),
    x=y_col,
    y=x_col,
    orientation='h',
    title="Óbitos por categoria"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# GRÁFICO TEMPORAL
# -----------------------------


# -----------------------------
# GRÁFICO PROPORÇÃO
# -----------------------------
st.subheader("🥧 Proporção")

fig2 = px.pie(
    top10,
    names=x_col,
    values=y_col,
    title="Distribuição percentual (Top 10)"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# NOTA EPIDEMIOLÓGICA
# -----------------------------
st.subheader("🧾 Nota Epidemiológica")

if st.button("Gerar Nota"):

    try:
        maior = df_filtrado.loc[df_filtrado[y_col].idxmax(), x_col]
    except:
        maior = "não identificado"

    texto = f"""
NOTA EPIDEMIOLÓGICA

Foram registrados {int(total)} óbitos por acidentes de trânsito no período analisado.

A maior concentração ocorreu em {maior}.

A taxa estimada foi de {taxa:.2f} óbitos por 100 mil habitantes.

Observa-se distribuição heterogênea entre as categorias analisadas.

LIMITAÇÕES:
- Dados agregados (TABNET)
- Possível subnotificação
- Não permite inferência individual (álcool/drogas)

RECOMENDAÇÕES:
- Intensificação da fiscalização
- Monitoramento contínuo
- Ações educativas
"""

    st.text_area("Nota gerada", texto, height=300)
