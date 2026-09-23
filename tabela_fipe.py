import pandas as pd
import streamlit as st

from carwiki import fipe, ui
from carwiki.utils import brl

st.title("Tabela FIPE")
st.caption("Preço médio de mercado por marca, modelo e ano. Dados da Tabela FIPE, consultados por uma API aberta "
           "(o site oficial veiculos.fipe.org.br não tem API pública).")

ref = ui.fipe_seletor("fipe")

if not ref:
    st.info("Escolha marca, modelo e ano para ver o preço.")
    st.stop()

st.metric(f"{ref['marca']} {ref['modelo']} {ref['ano']}", ref["preco_txt"])
st.markdown(
    f"**Combustível:** {ref['combustivel']}  \n"
    f"**Código FIPE:** {ref['codigo_fipe']}  \n"
    f"**Mês de referência:** {ref['mes']}"
)

st.subheader("Preço por ano")
st.caption("Faz uma consulta por ano do modelo, então gasta mais da cota diária da API.")
if st.button("Ver preço de todos os anos deste modelo"):
    try:
        with st.spinner("Consultando cada ano..."):
            dados = fipe.precos_por_ano(ref["marca_id"], ref["modelo_id"])
        tabela = pd.DataFrame(dados)
        tabela["preco_fmt"] = tabela["preco"].map(brl)
        st.bar_chart(tabela.set_index("ano")["preco"])
        st.dataframe(
            tabela.rename(columns={"ano": "Ano", "combustivel": "Combustível", "preco_fmt": "Preço"})[["Ano", "Combustível", "Preço"]],
            hide_index=True,
        )
    except fipe.FipeErro as e:
        st.warning(str(e))
