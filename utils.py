"""Funções pequenas usadas pelo resto do projeto."""
from __future__ import annotations

import html
import os
import re
from urllib.parse import urlparse


def get_secret(nome: str, padrao=None):
    """Lê um segredo do Streamlit (Secrets do Cloud) ou de variável de ambiente."""
    try:
        import streamlit as st

        if nome in st.secrets:
            return st.secrets[nome]
    except Exception:
        pass
    return os.environ.get(nome, padrao)


def cached(ttl: int = 3600):
    """Usa st.cache_data quando o Streamlit está presente; sem cache nos testes."""
    try:
        import streamlit as st

        return st.cache_data(ttl=ttl, show_spinner=False)
    except Exception:
        return lambda funcao: funcao


def esc(texto) -> str:
    """Escapa texto de fora (sites, IA) antes de colocar em HTML."""
    return html.escape("" if texto is None else str(texto), quote=True)


def md_seguro(texto) -> str:
    """Tira caracteres que quebram ou sequestram Markdown."""
    return re.sub(r"[\[\]()<>`*_|]", "", "" if texto is None else str(texto)).strip()


def url_segura(url) -> str:
    """Só aceita links http(s)."""
    url = (url or "").strip()
    return url if url.startswith(("http://", "https://")) else ""


def dominio_de(url: str) -> str:
    host = urlparse(url or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def para_float(valor) -> float:
    """Converte '45900.00', '45.900,00', 'R$ 45.900' ou 45900 em float. Erro vira 0."""
    if isinstance(valor, bool):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        s = str(valor).replace("R$", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
            s = s.replace(".", "")
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def brl(valor) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "Sob consulta"
    if v <= 0:
        return "Sob consulta"
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def numero_br(valor) -> str:
    """8.9 vira '8,9'; 4500 vira '4.500'."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if v == int(v):
        return f"{int(v):,}".replace(",", ".")
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
