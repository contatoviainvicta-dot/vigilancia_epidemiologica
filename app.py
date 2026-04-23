from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data"

def carregar_dados(arquivo):
    caminho = DATA_PATH / arquivo

    print(f"Abrindo arquivo: {caminho}")

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho, sep=";", encoding="latin1")

    return df

# =========================
# CONFIGURAÇÕES INICIAIS
# =========================
DATA_PATH = Path("data")

doencas = {
    "Hanseníase": "hanseniase.csv",
    "Tuberculose": "tuberculose.csv",
    "Leishmaniose Visceral": "leishmaniose_visceral.csv",
    "Leishmaniose Tegumentar": "leishmaniose_tegumentar.csv"
}

# =========================
# FUNÇÃO PARA LIMPEZA
# =========================
def carregar_dados(arquivo):
    df = pd.read_csv(DATA_PATH / arquivo, sep=";", encoding="latin1")

    # Remove colunas desnecessárias comuns do TabNet
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Padroniza nomes
    df.columns = df.columns.str.strip()

    return df


# =========================
# TRANSFORMAÇÃO DOS DADOS
# =========================
def transformar_para_longo(df):
    # Assume que colunas são anos (ex: 2015, 2016...)
    df_long = df.melt(id_vars=[df.columns[0]], var_name="Ano", value_name="Casos")

    df_long.rename(columns={df.columns[0]: "Categoria"}, inplace=True)

    df_long["Ano"] = pd.to_numeric(df_long["Ano"], errors="coerce")
    df_long["Casos"] = pd.to_numeric(df_long["Casos"], errors="coerce")

    df_long.dropna(inplace=True)

    return df_long


# =========================
# ANÁLISE TEMPORAL
# =========================
def analisar_tendencia(df, nome_doenca):
    df_total = df.groupby("Ano")["Casos"].sum().reset_index()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df_total, x="Ano", y="Casos", marker="o")

    plt.title(f"Tendência Temporal - {nome_doenca} (DF)")
    plt.xlabel("Ano")
    plt.ylabel("Número de Casos")
    plt.grid()

    plt.tight_layout()
    plt.show()

    return df_total


# =========================
# PERFIL EPIDEMIOLÓGICO
# =========================
def perfil_epidemiologico(df, nome_doenca):
    top = df.groupby("Categoria")["Casos"].sum().sort_values(ascending=False).head(10)

    plt.figure(figsize=(10, 5))
    sns.barplot(x=top.values, y=top.index)

    plt.title(f"Perfil Epidemiológico - {nome_doenca}")
    plt.xlabel("Casos")
    plt.ylabel("Categoria")

    plt.tight_layout()
    plt.show()


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
def main():
    resultados = {}

    for nome, arquivo in doencas.items():
        print(f"\n🔎 Analisando {nome}...")

        df = carregar_dados(arquivo)
        df_long = transformar_para_longo(df)

        tendencia = analisar_tendencia(df_long, nome)
        perfil_epidemiologico(df_long, nome)

        resultados[nome] = tendencia

    # =========================
    # COMPARAÇÃO ENTRE DOENÇAS
    # =========================
    print("\n📊 Comparando doenças...")

    df_comparado = pd.DataFrame()

    for nome, df in resultados.items():
        df_temp = df.copy()
        df_temp.rename(columns={"Casos": nome}, inplace=True)

        if df_comparado.empty:
            df_comparado = df_temp
        else:
            df_comparado = pd.merge(df_comparado, df_temp, on="Ano", how="outer")

    df_comparado.set_index("Ano").plot(figsize=(10, 6), marker="o")

    plt.title("Comparação entre Doenças Negligenciadas - DF")
    plt.ylabel("Casos")
    plt.grid()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
