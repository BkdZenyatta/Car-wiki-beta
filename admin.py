import streamlit as st

from carwiki import logs
from carwiki.utils import get_secret

st.title("Admin")

senha_certa = get_secret("ADMIN_PASSWORD")
if not senha_certa:
    st.warning("Essa página está desativada. Para ativar, defina **ADMIN_PASSWORD** nos "
               "Secrets do Streamlit (Settings > Secrets no Streamlit Cloud, ou "
               "`.streamlit/secrets.toml` local).")
    st.stop()

if not st.session_state.get("admin_ok"):
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == str(senha_certa):
            st.session_state["admin_ok"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

st.caption("Avisos técnicos das buscas (sites que falharam, páginas bloqueadas). "
           "Não aparecem para quem usa o site normalmente.")

c1, c2 = st.columns([5, 1])
if c2.button("Sair"):
    st.session_state["admin_ok"] = False
    st.rerun()

registros = logs.listar()
if not registros:
    st.info("Nenhum aviso registrado ainda.")
else:
    st.caption(f"{len(registros)} registro(s).")
    st.dataframe(
        [{"Quando": r["quando"], "Contexto": r["contexto"], "Aviso": r["mensagem"]} for r in registros],
        hide_index=True, use_container_width=True,
    )
    if st.button("Limpar registros"):
        logs.limpar()
        st.rerun()
