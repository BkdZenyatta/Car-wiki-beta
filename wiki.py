"""Monta a ficha de um carro: pesquisa nos sites de ficha técnica e pede para a IA organizar."""
from __future__ import annotations

from . import ai
from .search import buscar_fichas
from .utils import cached


@cached(86400)
def obter_ficha(nome: str) -> dict:
    """{"nome", "resumo", "specs", "fontes"}. Erros não ficam em cache."""
    nome = nome.strip()
    if not ai.ia_disponivel():
        raise RuntimeError("Falta a chave ANTHROPIC_API_KEY nos Secrets do Streamlit.")
    paginas = buscar_fichas(nome)
    if not paginas:
        raise LookupError(
            "Não achei páginas com ficha técnica para esse carro. "
            "Tente incluir marca, modelo, versão e ano (ex.: Toyota Corolla XEi 2.0 2020)."
        )
    ficha = ai.extrair_ficha(nome, paginas)
    ficha["nome"] = nome
    ficha["fontes"] = [{"fonte": p["fonte"], "titulo": p["titulo"], "url": p["url"]} for p in paginas]
    return ficha
