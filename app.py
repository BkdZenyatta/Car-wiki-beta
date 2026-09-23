"""Car Wiki: pesquisa de carros em estilo wiki.

Rodar localmente:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Car Wiki", page_icon=":material/directions_car:", layout="wide")

from carwiki import ui  # noqa: E402  (depois do set_page_config, que precisa vir primeiro)

ui.inject_css()

paginas = st.navigation(
    [
        st.Page("views/buscar.py", title="Buscar carros", icon=":material/search:", default=True),
        st.Page("views/wiki.py", title="Wiki do carro", icon=":material/menu_book:"),
        st.Page("views/comparar.py", title="Comparar", icon=":material/compare_arrows:"),
        st.Page("views/tabela_fipe.py", title="Tabela FIPE", icon=":material/payments:"),
    ]
)
paginas.run()
