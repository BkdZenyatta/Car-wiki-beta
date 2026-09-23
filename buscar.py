from datetime import date

import streamlit as st

from carwiki import config, ui
from carwiki.search import buscar_anuncios

ANO_MAX = date.today().year + 1
LIMITE_CARTOES = 30

st.title("Buscar carros")
st.caption("Anúncios de sites de carros, com endereço, filtros e comparação com a Tabela FIPE.")

# pedido vindo de outra página (botão "Buscar anúncios deste carro")
pedido = st.session_state.pop("busca_pedido", None)
if pedido:
    st.session_state["termo_busca"] = pedido

sites = config.chaves_por_papel("anuncios")

with st.sidebar:
    st.header("Busca")
    with st.form("form_busca"):
        termo = st.text_input("Marca e modelo", key="termo_busca", placeholder="Ex.: Honda Civic 2015")
        fontes = st.multiselect("Sites", sites, default=sites, format_func=lambda k: config.FONTES[k]["nome"])
        detalhar = st.checkbox(
            "Buscar foto e endereço na página do anúncio", value=True,
            help="Fica mais lento, mas traz fotos e endereços quando o site deixa.",
        )
        enviar = st.form_submit_button("Buscar")

if enviar or (pedido and termo.strip()):
    if not termo.strip():
        st.warning("Digite a marca e o modelo do carro.")
    elif not fontes:
        st.warning("Escolha pelo menos um site.")
    else:
        try:
            with st.spinner("Pesquisando nos sites escolhidos..."):
                anuncios, avisos = buscar_anuncios(termo.strip(), tuple(fontes), detalhar)
            st.session_state["busca"] = {"termo": termo.strip(), "anuncios": anuncios, "avisos": avisos}
        except Exception as e:  # noqa: BLE001
            st.error(f"A busca falhou: {e}")

with st.sidebar:
    st.header("Filtros")
    ano_min, ano_max = st.slider("Ano", 1990, ANO_MAX, (1990, ANO_MAX))
    preco_max = st.number_input("Preço máximo (R$)", min_value=0, value=0, step=5000, help="0 = sem limite")
    km_max = st.number_input("Quilometragem máxima", min_value=0, value=0, step=10000, help="0 = sem limite")
    uf = st.selectbox("Estado", ["Todos"] + list(config.ESTADOS), format_func=lambda u: u if u == "Todos" else f"{u} - {config.ESTADOS[u]}")
    cidade = st.text_input("Cidade", placeholder="Ex.: Novo Hamburgo")
    cambio = st.selectbox("Câmbio", ["Todos", "Automático", "Manual"])
    combustivel = st.selectbox("Combustível", ["Todos", "Flex", "Gasolina", "Diesel", "Etanol", "Elétrico", "Híbrido"])
    rigoroso = st.toggle("Esconder anúncios com dados faltando", value=False,
                         help="Sem isso, anúncio sem ano, km ou local passa pelos filtros.")
    com_paginas = st.toggle("Mostrar páginas sem preço", value=False,
                            help="Resultados que parecem listas ou páginas do site, não anúncios.")
    with st.expander("Comparar com a FIPE"):
        ref = ui.fipe_seletor("busca")


def passa(a: dict) -> bool:
    """Dado que falta no anúncio passa pelo filtro, a menos que "esconder dados faltando" esteja ligado."""
    if a["tipo"] == "pagina" and not com_paginas:
        return False

    def ok(valor, teste) -> bool:
        if valor in (None, ""):
            return not rigoroso
        return teste(valor)

    if (ano_min > 1990 or ano_max < ANO_MAX) and not ok(a.get("ano"), lambda v: ano_min <= v <= ano_max):
        return False
    if preco_max and not ok(a.get("preco") or None, lambda v: v <= preco_max):
        return False
    if km_max and not ok(a.get("km"), lambda v: v <= km_max):
        return False
    if uf != "Todos" and not ok(a.get("uf"), lambda v: v == uf):
        return False
    if cidade.strip():
        local = f"{a.get('cidade', '')} {a.get('endereco', '')}".strip().lower()
        if not ok(local, lambda v: cidade.strip().lower() in v):
            return False
    if cambio != "Todos" and not ok(a.get("cambio"), lambda v: v == cambio):
        return False
    if combustivel != "Todos" and not ok(a.get("combustivel"), lambda v: combustivel.lower() in v.lower()):
        return False
    return True


busca = st.session_state.get("busca")
if not busca:
    st.info("Digite a marca e o modelo na barra lateral e clique em Buscar. "
            "Depois use os filtros para refinar por ano, preço, quilometragem e local.")
    st.stop()

for aviso in busca["avisos"]:
    st.warning(aviso)

visiveis = [a for a in busca["anuncios"] if passa(a)]

ordenacoes = {
    "Menor preço": lambda a: (a["preco"] <= 0, a["preco"]),
    "Maior preço": lambda a: (a["preco"] <= 0, -a["preco"]),
    "Mais novo": lambda a: -(a.get("ano") or 0),
    "Menor quilometragem": lambda a: (a.get("km") is None, a.get("km") or 0),
}
if ref:
    ordenacoes["Mais abaixo da FIPE"] = lambda a: (a["preco"] <= 0, (a["preco"] / ref["preco"]) if ref["preco"] else 0)

c1, c2 = st.columns([3, 1])
c1.subheader(f"{len(visiveis)} resultado(s) para “{busca['termo']}”")
ordem = c2.selectbox("Ordenar por", list(ordenacoes), label_visibility="collapsed")

if ref:
    st.info(f"Referência FIPE: {ref['marca']} {ref['modelo']} {ref['ano']} ({ref['combustivel']}) — "
            f"{ref['preco_txt']} em {ref['mes']}. Confira se o anúncio é dessa mesma versão e ano.")

if not visiveis:
    st.info("Nenhum resultado com esses filtros. Afrouxe os filtros ou ative “Mostrar páginas sem preço”.")

for i, anuncio in enumerate(sorted(visiveis, key=ordenacoes[ordem])[:LIMITE_CARTOES]):
    ui.cartao_anuncio(anuncio, i, ref)

if len(visiveis) > LIMITE_CARTOES:
    st.caption(f"Mostrando os primeiros {LIMITE_CARTOES}. Use os filtros para chegar nos outros.")
