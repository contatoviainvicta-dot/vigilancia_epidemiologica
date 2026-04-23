import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.title("📊 Vigilância Epidemiológica - Leptospirose (DF)")

# =========================
# UPLOAD DO ARQUIVO
# =========================
arquivo = st.file_uploader("📂 Envie o CSV do TabNet", type=["csv"])

# =========================
# FUNÇÃO DE LEITURA ROBUSTA
# =========================
def carregar_dados(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
    except:
        df = pd.read_csv(uploaded_file, sep=";", encoding="latin1", engine="python")

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.columns = df.columns.str.strip()
    df.replace("-", pd.NA, inplace=True)
    df.dropna(how="all", inplace=True)

    return df


# =========================
# TRANSFORMAÇÃO
# =========================
def transformar_para_longo(df):
    coluna_base = df.columns[0]

    df_long = df.melt(
        id_vars=[coluna_base],
        var_name="Variavel",
        value_name="Casos"
    )

    df_long.rename(columns={coluna_base: "Categoria"}, inplace=True)

    df_long["Casos"] = pd.to_numeric(df_long["Casos"], errors="coerce")
    df_long.dropna(inplace=True)

    return df_long


# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:
    st.success("✅ Arquivo carregado!")

    df = carregar_dados(arquivo)

    st.subheader("📄 Preview dos dados")
    st.write(df.head())

    df_long = transformar_para_longo(df)

    # =========================
    # GRÁFICO DE TENDÊNCIA
    # =========================
    st.subheader("📈 Tendência Temporal")

    df_long["Categoria"] = pd.to_numeric(df_long["Categoria"], errors="coerce")
    df_long = df_long.dropna()

    df_total = df_long.groupby("Categoria")["Casos"].sum().reset_index()

    fig, ax = plt.subplots()
    sns.lineplot(data=df_total, x="Categoria", y="Casos", marker="o", ax=ax)

    ax.set_xlabel("Ano")
    ax.set_ylabel("Casos")
    ax.set_title("Leptospirose - DF")

    st.pyplot(fig)

    # =========================
    # PERFIL
    # =========================
    st.subheader("📊 Perfil Epidemiológico")

    df_perf = df_long.groupby("Variavel")["Casos"].sum().reset_index()
    df_perf = df_perf.sort_values(by="Casos", ascending=False).head(10)

    fig2, ax2 = plt.subplots()
    sns.barplot(data=df_perf, x="Casos", y="Variavel", ax=ax2)

    st.pyplot(fig2)

else:
    st.info("⬆️ Faça upload de um arquivo CSV do TabNet para começar")
