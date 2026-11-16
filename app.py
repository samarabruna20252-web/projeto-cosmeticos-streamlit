import streamlit as st
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================

st.set_page_config(
    page_title="L'Oréal Beauty Store",
    page_icon="💄",
    layout="wide"
)

# ==========================================
# 2. IDENTIDADE VISUAL
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #FAF8F8;
    }

    [data-testid="stSidebar"] {
        background-color: #28151F;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    h1, h2, h3 {
        color: #351724;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E8DCE1;
        padding: 18px;
        border-radius: 12px;
    }

    div[data-testid="stMetricValue"] {
        color: #761F43;
    }

    .subtitulo {
        color: #795C69;
        font-size: 16px;
    }

    hr {
        border-color: #E8DCE1;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CARREGAMENTO DOS DADOS
# ==========================================

caminho_csv = Path(__file__).parent / "produtos_cosmeticos_ficticios.csv"

try:
    produtos = pd.read_csv(caminho_csv)
except FileNotFoundError:
    st.error("Não foi possível encontrar o arquivo CSV.")
    st.stop()

colunas_obrigatorias = [
    "produto",
    "marca",
    "estoque_atual",
    "estoque_minimo",
    "estoque_alvo",
    "custo_compra"
]

faltantes = [
    coluna for coluna in colunas_obrigatorias
    if coluna not in produtos.columns
]

if faltantes:
    st.error(f"Colunas ausentes no CSV: {faltantes}")
    st.stop()

# ==========================================
# 4. CÁLCULOS DO ESTOQUE
# ==========================================

produtos["estoque_atual"] = pd.to_numeric(
    produtos["estoque_atual"], errors="coerce"
).fillna(0)

produtos["estoque_minimo"] = pd.to_numeric(
    produtos["estoque_minimo"], errors="coerce"
).fillna(0)

produtos["estoque_alvo"] = pd.to_numeric(
    produtos["estoque_alvo"], errors="coerce"
).fillna(0)

produtos["custo_compra"] = pd.to_numeric(
    produtos["custo_compra"], errors="coerce"
).fillna(0)

produtos["quantidade_comprar"] = (
    produtos["estoque_alvo"] - produtos["estoque_atual"]
).clip(lower=0)

produtos["custo_reposicao"] = (
    produtos["quantidade_comprar"] * produtos["custo_compra"]
)

produtos["situacao"] = produtos.apply(
    lambda linha: "Reposição necessária"
    if linha["estoque_atual"] < linha["estoque_minimo"]
    else "Estoque adequado",
    axis=1
)

produtos_baixo_estoque = produtos[
    produtos["estoque_atual"] < produtos["estoque_minimo"]
].copy()

valor_estoque = (
    produtos["estoque_atual"] * produtos["custo_compra"]
).sum()

custo_reposicao = produtos_baixo_estoque[
    "custo_reposicao"
].sum()

# ==========================================
# 5. MENU LATERAL E FILTROS
# ==========================================

st.sidebar.title("💄 L'ORÉAL")
st.sidebar.caption("BEAUTY STORE")
st.sidebar.divider()

pagina = st.sidebar.radio(
    "Navegação",
    ["Visão geral", "Produtos", "Planejamento de compras"]
)

st.sidebar.divider()
st.sidebar.subheader("Filtros")

marcas = sorted(produtos["marca"].dropna().unique())

marcas_selecionadas = st.sidebar.multiselect(
    "Selecione as marcas",
    marcas,
    default=marcas
)

if "categoria" in produtos.columns:
    categorias = sorted(
        produtos["categoria"].dropna().unique()
    )

    categorias_selecionadas = st.sidebar.multiselect(
        "Selecione as categorias",
        categorias,
        default=categorias
    )

    produtos_filtrados = produtos[
        produtos["marca"].isin(marcas_selecionadas)
        & produtos["categoria"].isin(categorias_selecionadas)
    ].copy()
else:
    produtos_filtrados = produtos[
        produtos["marca"].isin(marcas_selecionadas)
    ].copy()

# ==========================================
# 6. CABEÇALHO
# ==========================================

st.title("💄 L'Oréal Beauty Store")

st.markdown(
    '<p class="subtitulo">Sistema de Gestão de Estoque e Planejamento de Compras</p>',
    unsafe_allow_html=True
)

st.divider()

# ==========================================
# 7. PÁGINA: VISÃO GERAL
# ==========================================

if pagina == "Visão geral":

    st.header("Visão geral do estoque")

    baixo_filtrado = produtos_filtrados[
        produtos_filtrados["estoque_atual"]
        < produtos_filtrados["estoque_minimo"]
    ]

    valor_filtrado = (
        produtos_filtrados["estoque_atual"]
        * produtos_filtrados["custo_compra"]
    ).sum()

    reposicao_filtrada = baixo_filtrado[
        "custo_reposicao"
    ].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Produtos cadastrados",
        len(produtos_filtrados)
    )

    col2.metric(
        "Produtos para reposição",
        len(baixo_filtrado)
    )

    col3.metric(
        "Valor do estoque",
        f"R$ {valor_filtrado:,.2f}"
    )

    col4.metric(
        "Custo de reposição",
        f"R$ {reposicao_filtrada:,.2f}"
    )

    st.divider()

    # Gráfico de produtos por marca

    st.subheader("Distribuição de produtos por marca")

    quantidade_marcas = (
        produtos_filtrados.groupby("marca")
        .size()
        .sort_values(ascending=False)
    )

    st.bar_chart(quantidade_marcas)

    # Gráfico por categoria, se disponível

    if "categoria" in produtos_filtrados.columns:

        st.subheader("Produtos por categoria")

        quantidade_categorias = (
            produtos_filtrados.groupby("categoria")
            .size()
        )

        st.bar_chart(quantidade_categorias)

    # Situação do estoque

    st.subheader("Situação do estoque")

    situacao = produtos_filtrados["situacao"].value_counts()

    st.bar_chart(situacao)

# ==========================================
# 8. PÁGINA: PRODUTOS
# ==========================================

elif pagina == "Produtos":

    st.header("Catálogo de produtos")

    busca = st.text_input(
        "🔎 Pesquisar produto",
        placeholder="Digite o nome de um produto..."
    )

    tabela_produtos = produtos_filtrados.copy()

    if busca:
        tabela_produtos = tabela_produtos[
            tabela_produtos["produto"].str.contains(
                busca, case=False, na=False
            )
        ]

    st.write(f"Total de produtos encontrados: {len(tabela_produtos)}")

    colunas_exibir = [
        coluna for coluna in [
            "produto",
            "marca",
            "categoria",
            "estoque_atual",
            "estoque_minimo",
            "custo_compra",
            "situacao"
        ]
        if coluna in tabela_produtos.columns
    ]

    st.dataframe(
        tabela_produtos[colunas_exibir],
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# 9. PÁGINA: PLANEJAMENTO DE COMPRAS
# ==========================================

elif pagina == "Planejamento de compras":

    st.header("⚠️ Planejamento de reposição")

    reposicao = produtos_filtrados[
        produtos_filtrados["estoque_atual"]
        < produtos_filtrados["estoque_minimo"]
    ].copy()

    st.write(
        "Produtos cujo estoque atual está abaixo do estoque mínimo."
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Produtos que precisam de compra",
        len(reposicao)
    )

    col2.metric(
        "Investimento necessário",
        f"R$ {reposicao['custo_reposicao'].sum():,.2f}"
    )

    st.divider()

    colunas_reposicao = [
        coluna for coluna in [
            "produto",
            "marca",
            "estoque_atual",
            "estoque_minimo",
            "quantidade_comprar",
            "custo_compra",
            "custo_reposicao"
        ]
        if coluna in reposicao.columns
    ]

    st.dataframe(
        reposicao[colunas_reposicao],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Investimento por marca")

    investimento_marca = (
        reposicao.groupby("marca")["custo_reposicao"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(investimento_marca)

    st.success(
        f"Investimento total estimado para reposição: "
        f"R$ {reposicao['custo_reposicao'].sum():,.2f}"
    )

# ==========================================
# 10. RODAPÉ
# ==========================================

st.divider()

st.caption(
    "L'Oréal Beauty Store | Projeto acadêmico de Engenharia de Produção"
)
