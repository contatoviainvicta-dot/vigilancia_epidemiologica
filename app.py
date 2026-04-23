import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Vigilância - Trânsito", layout="wide")

st.title("🚗 Monitoramento de Mortalidade por Acidentes de Trânsito")
st.markdown("Análise baseada em dados do SIM/DATASUS (TABNET ou estruturados)")

# -----------------------------
# UPLOAD
# -----------------------------
arquivo = st.file_uploader("Envie o arquivo (CSV ou Excel)", type=["csv", "xlsx"])

if arquivo is None:
    st.info("Aguardando upload do arquivo...")
    st.stop()

# -----------------------------
# DEBUG (opcional)
# -----------------------------
st.write("📄 Nome:", arquivo.name)
st.write("📦 Tipo:", arquivo.type)

conteudo_bytes = arquivo.getvalue()

# -----------------------------
# FUNÇÃO PRINCIPAL DE LEITURA
# -----------------------------
def carregar_dados(conteudo_bytes, nome_arquivo):
    
    # 1. Tentar Excel direto
    try:
        df = pd.read_excel(io.BytesIO(conteudo_bytes))
        if df.shape[1] > 1:
            return df
    except:
        pass

    # 2. Decodificar texto
    texto = None
    for enc in ['latin-1', 'utf-8', 'cp1252']:
        try:
            texto = conteudo_bytes.decode(enc)
            break
        except:
            continue

    if texto is None:
        raise Exception("Não foi possível decodificar o arquivo.")

    linhas = texto.splitlines()

    # 3. Detectar TABNET (pular cabeçalho sujo)
    inicio_dados = 0
    for i, linha in enumerate(linhas):
        if "Munic" in linha or "Município" in linha:
            inicio_dados = i
            break

    dados_limpos = "\n".join(linhas[inicio_dados:])

    # 4. Tentar CSV com ;
    try:
        df = pd.read_csv(io.StringIO(dados_limpos), sep=';')
        if df.shape[1] > 1:
            return df
    except:
        pass

    # 5. Tentar CSV com ,
    try:
        df = pd.read_csv(io.StringIO(dados_limpos), sep=',')
        if df.shape[1] > 1:
            return df
    except:
        pass

    raise Exception("Formato não reconhecido.")

# -----------------------------
# CARREGAMENTO
# -----------------------------
try:
    df = carregar_dados(conteudo_bytes, arquivo.name)
except Exception as e:
    st.error(f"Erro ao carregar arquivo: {e}")
    st.stop()

# -----------------------------
# VISUALIZAÇÃO INICIAL
# -----------------------------
st.subheader("🔎 Dados carregados")

st.write("Shape:", df.shape)
st.write("Colunas:", df.columns.tolist())

st.dataframe(df.head())

# -----------------------------
# ANÁLISE AUTOMÁTICA (TABNET)
# -----------------------------
st.subheader("📊 Análise descritiva")

colunas = df.columns.tolist()

if len(colunas) >= 2:
    x_col = colunas[0]
    y_col = colunas[1]

    # Tentar converter valores
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} por {x_col}"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Não foi possível identificar colunas suficientes para análise.")

# -----------------------------
# TABELA RESUMO
# -----------------------------
st.subheader("📈 Estatísticas")

try:
    total = df[y_col].sum()
    media = df[y_col].mean()

    col1, col2 = st.columns(2)
    col1.metric("Total", int(total))
    col2.metric("Média", round(media, 2))

except:
    st.warning("Não foi possível calcular estatísticas.")

# -----------------------------
# NOTA EPIDEMIOLÓGICA
# -----------------------------
st.subheader("🧾 Nota Epidemiológica")

if st.button("Gerar Nota"):
    texto = f"""
NOTA EPIDEMIOLÓGICA

Foram analisados dados de mortalidade por acidentes de trânsito provenientes do DATASUS.

Total de registros: {df.shape[0]}
Total de óbitos: {int(total) if 'total' in locals() else 'N/A'}

Observa-se distribuição variável entre categorias analisadas.

LIMITAÇÕES:
- Dados agregados (TABNET)
- Possível subnotificação
- Ausência de variáveis individuais (ex: álcool/drogas)

IMPLICAÇÕES:
- Monitoramento contínuo
- Apoio a políticas públicas de segurança no trânsito
"""

    st.text_area("Texto gerado", texto, height=300)
