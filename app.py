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
    import io

    # Lê conteúdo bruto
    content = uploaded_file.read().decode("latin1")

    # Debug (MOSTRA no app)
    st.subheader("🔍 Conteúdo bruto (início do arquivo)")
    st.text(content[:500])

    # Detecta automaticamente separador
    if ";" in content:
        sep = ";"
    elif "," in content:
        sep = ","
    elif "\t" in content:
        sep = "\t"
    else:
        st.error("❌ Não foi possível identificar o separador do CSV")
        return None

    st.info(f"Separador detectado: '{sep}'")

    # Reconstrói arquivo para leitura
    data = io.StringIO(content)

    df = pd.read_csv(
        data,
        sep=sep,
        engine="python",
        on_bad_lines="skip"
    )

    # Limpeza
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.columns = df.columns.str.strip()
    df.replace("-", pd.NA, inplace=True)
    df.dropna(how="all", inplace=True)

    # Verificação crítica
    if df.shape[1] == 0:
        st.error("❌ Arquivo não contém colunas válidas")
        return None

    st.success("✅ CSV lido com sucesso")
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
