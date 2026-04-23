import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# =========================
# CONFIGURAÇÃO DE CAMINHO
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data"

# =========================
# CONFIGURAÇÃO DAS DOENÇAS
# =========================
doencas = {
    "Leptospirose": "leptospirose.csv"
}

# =========================
# FUNÇÃO DE LEITURA SEGURA
# =========================
def carregar_dados(arquivo):
    caminho = DATA_PATH / arquivo

    print(f"\n🔎 Abrindo: {caminho}")

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        # tentativa padrão
        df = pd.read_csv(caminho, sep=";", encoding="latin1")
    except Exception as e:
        print("⚠️ Erro na leitura padrão, tentando modo robusto...")

        df = pd.read_csv(
            caminho,
            sep=";",
            encoding="latin1",
            engine="python",
            skiprows=1  # ignora cabeçalho extra do TabNet
        )

    # remove colunas vazias
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # limpa nomes
    df.columns = df.columns.str.strip()

    # remove linhas totalmente vazias
    df.dropna(how="all", inplace=True)

    # substitui "-" por NaN
    df.replace("-", pd.NA, inplace=True)

    print("✅ Dados carregados")
    print(df.head())

    return df


# =========================
# TRANSFORMA PARA FORMATO LONGO
# =========================
def transformar_para_longo(df):
    # Assume que a primeira coluna é categoria (ex: Ano)
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
# TENDÊNCIA TEMPORAL
# =========================
def grafico_tendencia(df, nome):
    # Tenta converter categoria para número (ano)
    df["Categoria"] = pd.to_numeric(df["Categoria"], errors="coerce")
    df = df.dropna()

    df_total = df.groupby("Categoria")["Casos"].sum().reset_index()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df_total, x="Categoria", y="Casos", marker="o")

    plt.title(f"Tendência Temporal - {nome} (DF)")
    plt.xlabel("Ano")
    plt.ylabel("Casos")
    plt.grid()

    plt.tight_layout()
    plt.show()

    print("\n📊 Dados agregados:")
    print(df_total)


# =========================
# PERFIL EPIDEMIOLÓGICO
# =========================
def grafico_perfil(df, nome):
    df_total = df.groupby("Variavel")["Casos"].sum().reset_index()

    df_total = df_total.sort_values(by="Casos", ascending=False).head(10)

    plt.figure(figsize=(10, 5))
    sns.barplot(data=df_total, x="Casos", y="Variavel")

    plt.title(f"Perfil Epidemiológico - {nome}")
    plt.xlabel("Casos")
    plt.ylabel("Categoria")

    plt.tight_layout()
    plt.show()


# =========================
# FUNÇÃO PRINCIPAL
# =========================
def main():
    print("\n🚀 INICIANDO ANÁLISE EPIDEMIOLÓGICA\n")

    for nome, arquivo in doencas.items():
        print(f"\n==============================")
        print(f"🦠 Doença: {nome}")
        print(f"==============================")

        df = carregar_dados(arquivo)
        df_long = transformar_para_longo(df)

        # Gráficos
        grafico_tendencia(df_long.copy(), nome)
        grafico_perfil(df_long.copy(), nome)

    print("\n✅ Análise concluída com sucesso!")


# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    main()
