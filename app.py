import streamlit as st
import pandas as pd
import plotly.express as px
import io

# =====================================
# CONFIG
# =====================================
st.set_page_config(page_title="Vigilância - Trânsito", layout="wide")

st.title("🚗 Monitoramento de Mortalidade por Acidentes de Trânsito")
st.markdown("Dados do SIM/DATASUS (TABNET ou estruturados)")

# =====================================
# FUNÇÕES
# =====================================

def carregar_dados(conteudo_bytes):
    try:
        df = pd.read_excel(io.BytesIO(conteudo_bytes))
        if df.shape[1] > 1:
            return df
    except:
        pass

    for enc in ['latin-1', 'utf-8', 'cp1252']:
        try:
            texto = conteudo_bytes.decode(enc)
            break
        except:
            continue
    else:
        raise Exception("Erro ao decodificar arquivo")

    linhas = texto.splitlines()

    for i, linha in enumerate(linhas):
        if linha.count(';') >= 1:
            inicio = i
            break
    else:
        raise Exception("Tabela não encontrada")

    dados_limpos = "\n".join(linhas[inicio:])
    return pd.read_csv(io.StringIO(dados_limpos), sep=';')


def transformar_tabnet(df):
    df = df.copy()
    df = df[~df.iloc[:, 0].astype(str).str.contains("Total", case=False)]
    df = df.rename(columns={df.columns[0]: "categoria"})

    df = df.melt(
        id_vars="categoria",
        var_name="ano",
        value_name="obitos"
    )

    df["obitos"] = pd.to_numeric(df["obitos"], errors="coerce")
    return df.dropna()


def preparar_mes(df):
    ordem = [
        "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
    ]

    df_mes = (
        df.groupby("categoria")["obitos"]
        .sum()
        .reset_index()
    )

    df_mes["categoria"] = pd.Categorical(df_mes["categoria"], categories=ordem, ordered=True)
    return df_mes.sort_values("categoria")


# =====================================
# UPLOAD
# =====================================
arquivo = st.file_uploader("Envie o arquivo (CSV ou Excel)", type=["csv", "xlsx"])

if arquivo is None:
    st.stop()

conteudo = arquivo.getvalue()

# =====================================
# CARREGAMENTO
# =====================================
try:
    df = carregar_dados(conteudo)
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

# Detectar TABNET
if df.shape[1] > 3:
    st.info("Formato TABNET detectado")
    df = transformar_tabnet(df)

# =====================================
# COLUNAS
# =====================================
x_col = "categoria"
y_col = "obitos"

# =====================================
# FILTRO
# =====================================
st.subheader("🔍 Filtro")
filtro = st.text_input("Filtrar")

df = df[df[x_col].astype(str).str.contains(filtro, case=False, na=False)]

# =====================================
# INDICADORES
# =====================================
st.subheader("📊 Indicadores")

pop = st.number_input("População", value=3000000)

total = df[y_col].sum()
media = df[y_col].mean()
taxa = (total / pop) * 100000 if pop > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total", int(total))
c2.metric("Média", round(media, 2))
c3.metric("Taxa/100 mil", f"{taxa:.2f}")

# =====================================
# DISTRIBUIÇÃO MENSAL
# =====================================
st.subheader("📅 Distribuição por mês")

df_mes = preparar_mes(df)
st.dataframe(df_mes)

fig_mes = px.bar(df_mes, x="categoria", y="obitos")
st.plotly_chart(fig_mes, use_container_width=True)

# =====================================
# RANKING
# =====================================
st.subheader("🔝 Ranking")

ranking = (
    df.groupby("categoria")["obitos"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

st.dataframe(ranking)

# =====================================
# ALERTA
# =====================================
limite = df[y_col].mean() + 2 * df[y_col].std()

if df[y_col].max() > limite:
    st.error("⚠️ Possível concentração elevada detectada")

# =====================================
# PROPORÇÃO (CORRIGIDO)
# =====================================
st.subheader("🥧 Proporção")

fig_pie = px.pie(
    ranking,
    names="categoria",
    values="obitos"
)

st.plotly_chart(fig_pie)

# =====================================
# NOTA
# =====================================
st.subheader("🧾 Nota Epidemiológica")

if st.button("Gerar"):
    maior = ranking.iloc[0]["categoria"]

    st.text_area("Nota", f"""
Foram registrados {int(total)} óbitos por acidentes de trânsito.

Maior concentração: {maior}

Taxa: {taxa:.2f}/100 mil hab

Limitações:
- Dados agregados
- Subnotificação
- Sem associação individual álcool/drogas
""", height=250)
