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
    import pandas as pd
    import io

    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    # Encontrar onde começa o cabeçalho real
    inicio = None
    for i, linha in enumerate(linhas):
        if "Ano" in linha and "Casos" in linha:
            inicio = i
            break

    if inicio is None:
        raise ValueError("❌ Não encontrou cabeçalho 'Ano / Casos'")

    # Ler apenas a parte útil
    dados = "\n".join(linhas[inicio:])

    df = pd.read_csv(
        io.StringIO(dados),
        sep=r"\s+",
        engine="python"
    )

    # Renomear colunas corretamente
    df.columns = ["Ano", "Casos"]

    # Remover linha "Total"
    df = df[df["Ano"] != "Total"]

    # Converter tipos
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Casos"] = pd.to_numeric(df["Casos"], errors="coerce")

    df.dropna(inplace=True)

    return df
# =========================
# TRANSFORMAÇÃO
# =========================
def preparar_dados_tabnet(df):
    # Mostrar colunas para debug
    st.write("Colunas detectadas:", df.columns.tolist())

    # Caso padrão TabNet: 2 colunas (Ano + Casos)
    if df.shape[1] == 2:
        df.columns = ["Ano", "Casos"]

    # Limpeza
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Casos"] = pd.to_numeric(df["Casos"], errors="coerce")

    df.dropna(inplace=True)

    return df


# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:
    st.success("✅ Arquivo carregado!")

    df = carregar_dados(arquivo)

    st.subheader("📄 Preview dos dados")
    st.write(df.head())

    df = preparar_dados_tabnet(df)
    # =========================
    # GRÁFICO DE TENDÊNCIA
    # =========================
    fig, ax = plt.subplots()

    sns.lineplot(data=df, x="Ano", y="Casos", marker="o", ax=ax)

    ax.set_title("Leptospirose - DF")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Casos")

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
