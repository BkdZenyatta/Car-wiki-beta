import streamlit as st

from carwiki import ai, ui
from carwiki.wiki import obter_ficha

MAX_CARROS = 4

st.title("Comparar carros")
st.caption("Compara as fichas técnicas lado a lado e destaca o melhor valor de cada linha.")

lista = st.session_state.setdefault("comparar", [])

with st.form("form_add", clear_on_submit=True):
    novo = st.text_input("Adicionar carro", placeholder="Ex.: Toyota Corolla XEi 2.0 2020")
    if st.form_submit_button("Adicionar"):
        novo = novo.strip()
        if len(lista) >= MAX_CARROS:
            st.warning(f"A comparação aceita até {MAX_CARROS} carros.")
        elif novo and novo not in lista:
            lista.append(novo)

for i, nome in enumerate(list(lista)):
    col_nome, col_botao = st.columns([6, 1])
    col_nome.write(nome)
    if col_botao.button("Remover", key=f"remover_{i}"):
        lista.pop(i)
        st.session_state.pop("comp_ativa", None)
        st.rerun()

if len(lista) < 2:
    st.info("Adicione pelo menos 2 carros. Também dá para usar o botão “Comparar” nos resultados da busca.")
    st.stop()

if not ai.ia_disponivel():
    st.warning("A comparação precisa da chave da IA (ANTHROPIC_API_KEY) para ler as fichas técnicas.")
    st.stop()

if st.button("Comparar"):
    st.session_state["comp_ativa"] = tuple(lista)

ativa = st.session_state.get("comp_ativa")
if not ativa:
    st.stop()

fichas, problemas = [], []
with st.status("Lendo as fichas técnicas...", expanded=False) as status:
    for nome in ativa:
        try:
            fichas.append(obter_ficha(nome))
        except Exception as e:  # noqa: BLE001
            fichas.append({"nome": nome, "specs": {}, "resumo": "", "fontes": []})
            problemas.append(f"{nome}: {e}")
    status.update(label="Fichas prontas", state="complete")

for problema in problemas:
    st.warning(problema)

st.subheader("Ficha técnica lado a lado")
st.markdown(ui.tabela_comparacao_html(list(ativa), fichas), unsafe_allow_html=True)
st.caption("Células em verde marcam o melhor valor da linha (mais potência, menor tempo de 0 a 100, menor peso etc.).")

com_dados = [{"nome": f["nome"], "specs": {k: v for k, v in f["specs"].items() if v is not None}}
             for f in fichas if any(v is not None for v in f["specs"].values())]
if len(com_dados) >= 2:
    st.subheader("Análise")
    try:
        with st.spinner("Escrevendo a análise..."):
            st.markdown(ai.comparar(com_dados))
    except Exception as e:  # noqa: BLE001
        st.warning(f"Não consegui escrever a análise: {e}")
