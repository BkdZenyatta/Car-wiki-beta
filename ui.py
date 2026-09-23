"""Peças de interface usadas por mais de uma página."""
from __future__ import annotations

import re

import streamlit as st

from . import config, fipe
from .search import nome_para_ficha
from .utils import brl, esc, numero_br, url_segura

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap');
:root { --cw-ink:#14181f; --cw-muted:#5b6472; --cw-line:#dfe3e8; --cw-panel:#f3f5f7;
        --cw-accent:#c8102e; --cw-good:#1a7f4b; --cw-bad:#b42318; --cw-link:#0b57d0; }
.stApp { font-family:'Inter', system-ui, sans-serif; }
h1, h2, h3 { font-family:'Source Serif 4', Georgia, serif !important; letter-spacing:-0.01em; }
h1 { border-bottom:1px solid var(--cw-line); padding-bottom:.35rem; }
.cw-titulo { font-size:1.05rem; font-weight:600; line-height:1.3; color:var(--cw-ink); }
.cw-titulo a { color:var(--cw-link); text-decoration:none; }
.cw-titulo a:hover { text-decoration:underline; }
.cw-preco { font-size:1.45rem; font-weight:600; color:var(--cw-ink); margin:.15rem 0; }
.cw-linha { color:var(--cw-muted); font-size:.9rem; margin:.2rem 0; }
.cw-linha b { color:var(--cw-ink); font-weight:500; }
.cw-tag { display:inline-block; background:var(--cw-panel); border:1px solid var(--cw-line);
          border-radius:4px; padding:1px 8px; margin:0 6px 4px 0; font-size:.8rem; }
.cw-fonte { display:inline-block; color:#fff; border-radius:4px; padding:1px 8px; font-size:.75rem; margin-right:6px; }
.cw-fipe { display:inline-block; border-radius:4px; padding:1px 8px; font-size:.78rem; font-weight:600; }
.cw-fipe.bom { background:#e3f4ea; color:var(--cw-good); }
.cw-fipe.ruim { background:#fdeceb; color:var(--cw-bad); }
.cw-fipe.neutro { background:#e8eefc; color:var(--cw-link); }
.cw-sem-foto { background:var(--cw-panel); color:var(--cw-muted); height:110px; display:flex;
               align-items:center; justify-content:center; border-radius:4px; font-size:.85rem; }
table.cw-infobox { width:100%; border:1px solid var(--cw-line); border-collapse:collapse; background:var(--cw-panel); font-size:.9rem; }
table.cw-infobox caption { caption-side:top; text-align:center; font-family:'Source Serif 4', Georgia, serif;
                           font-weight:700; font-size:1.05rem; padding:.6rem .5rem; background:#e6e9ee;
                           border:1px solid var(--cw-line); border-bottom:none; }
table.cw-infobox th { text-align:left; font-weight:500; color:var(--cw-muted); padding:.35rem .6rem; width:45%; vertical-align:top; }
table.cw-infobox td { padding:.35rem .6rem; color:var(--cw-ink); }
table.cw-infobox tr + tr > * { border-top:1px solid var(--cw-line); }
.cw-scroll { overflow-x:auto; }
table.cw-comp { width:100%; border-collapse:collapse; font-size:.92rem; }
table.cw-comp th, table.cw-comp td { border:1px solid var(--cw-line); padding:.45rem .7rem; text-align:left; }
table.cw-comp thead th { background:var(--cw-panel); font-weight:600; }
table.cw-comp tbody th { font-weight:500; color:var(--cw-muted); background:#fafbfc; }
table.cw-comp td.melhor { background:#e3f4ea; font-weight:600; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ formatação
def formatar_valor(valor, unidade: str = "") -> str:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        texto = numero_br(valor)
    else:
        texto = str(valor)
    return f"{texto} {unidade}".strip()


def endereco_do_anuncio(a: dict) -> str:
    if a.get("endereco"):
        return a["endereco"]
    if a.get("cidade") and a.get("uf"):
        return f"{a['cidade']} - {a['uf']}"
    return a.get("uf") or ""


def _selo_fipe(a: dict, ref: dict | None) -> str:
    if not ref or not ref.get("preco") or not a.get("preco"):
        return ""
    dif = (a["preco"] - ref["preco"]) / ref["preco"] * 100
    if abs(dif) <= 5:
        return '<span class="cw-fipe neutro">Na faixa da FIPE</span>'
    if dif < 0:
        return f'<span class="cw-fipe bom">{abs(dif):.0f}% abaixo da FIPE</span>'
    return f'<span class="cw-fipe ruim">{dif:.0f}% acima da FIPE</span>'


def _html_cartao(a: dict, ref: dict | None) -> str:
    cor = a.get("cor", "#475569")
    cor = cor if re.fullmatch(r"#[0-9a-fA-F]{6}", cor) else "#475569"
    url = url_segura(a.get("url"))
    titulo = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(a["titulo"])}</a>' if url else esc(a["titulo"])
    tags = []
    if a.get("ano"):
        tags.append(str(a["ano"]))
    if a.get("km") is not None:
        tags.append(f"{numero_br(a['km'])} km")
    tags += [t for t in (a.get("cambio"), a.get("combustivel")) if t]
    tags_html = "".join(f'<span class="cw-tag">{esc(t)}</span>' for t in tags)
    local = endereco_do_anuncio(a)
    linha_local = f'<div class="cw-linha"><b>Endereço:</b> {esc(local)}</div>' if local else \
        '<div class="cw-linha">Endereço não informado no anúncio</div>'
    return (
        f'<div class="cw-titulo">{titulo}</div>'
        f'<div class="cw-preco">{esc(brl(a.get("preco")))} {_selo_fipe(a, ref)}</div>'
        f"<div>{tags_html}</div>{linha_local}"
        f'<div class="cw-linha"><span class="cw-fonte" style="background:{cor}">{esc(a.get("fonte", ""))}</span></div>'
    )


def adicionar_comparacao(nome: str) -> None:
    lista = st.session_state.setdefault("comparar", [])
    if nome in lista:
        st.toast("Esse carro já está na comparação.")
    elif len(lista) >= 4:
        st.toast("A comparação aceita até 4 carros.")
    else:
        lista.append(nome)
        st.toast(f"Adicionado à comparação: {nome}")


def cartao_anuncio(a: dict, idx: int, ref: dict | None = None) -> None:
    with st.container(border=True):
        col_foto, col_info = st.columns([1, 3])
        with col_foto:
            foto = url_segura(a.get("thumb"))
            if foto:
                st.image(foto)
            else:
                st.markdown('<div class="cw-sem-foto">Sem foto</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(_html_cartao(a, ref), unsafe_allow_html=True)
            b1, b2, b3, _ = st.columns([1.3, 1.3, 1.3, 3])
            if url_segura(a.get("url")):
                b1.link_button("Abrir anúncio", a["url"])
            nome = nome_para_ficha(a["titulo"]) or a["titulo"]
            if b2.button("Ficha técnica", key=f"ficha_{idx}"):
                st.session_state["wiki_pedido"] = nome
                st.switch_page("views/wiki.py")
            if b3.button("Comparar", key=f"comp_{idx}"):
                adicionar_comparacao(nome)


# ---------------------------------------------------------------- wiki / tabela
def infobox_html(nome: str, specs: dict) -> str:
    linhas = []
    for chave, rotulo, unidade, _ in config.ESPECIFICACOES:
        valor = specs.get(chave)
        if valor in (None, ""):
            continue
        linhas.append(f"<tr><th>{esc(rotulo)}</th><td>{esc(formatar_valor(valor, unidade))}</td></tr>")
    corpo = "".join(linhas) or '<tr><td colspan="2">Nenhum dado encontrado nas páginas lidas.</td></tr>'
    return f'<table class="cw-infobox"><caption>{esc(nome)}</caption>{corpo}</table>'


def _indices_melhores(valores: list, melhor: str | None) -> set[int]:
    numeros = [(i, float(v)) for i, v in enumerate(valores)
               if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if melhor is None or len(numeros) < 2:
        return set()
    alvo = max(n for _, n in numeros) if melhor == "max" else min(n for _, n in numeros)
    if all(n == alvo for _, n in numeros):
        return set()
    return {i for i, n in numeros if n == alvo}


def tabela_comparacao_html(nomes: list[str], fichas: list[dict]) -> str:
    cabecalho = "".join(f"<th>{esc(n)}</th>" for n in nomes)
    linhas = []
    for chave, rotulo, unidade, melhor in config.ESPECIFICACOES:
        valores = [(f.get("specs") or {}).get(chave) for f in fichas]
        if all(v in (None, "") for v in valores):
            continue
        destaque = _indices_melhores(valores, melhor)
        celulas = "".join(
            f'<td class="{"melhor" if i in destaque else ""}">'
            f'{esc(formatar_valor(v, unidade)) if v not in (None, "") else "—"}</td>'
            for i, v in enumerate(valores)
        )
        linhas.append(f"<tr><th>{esc(rotulo)}</th>{celulas}</tr>")
    if not linhas:
        return "<p>Nenhum dado de ficha técnica encontrado.</p>"
    return (f'<div class="cw-scroll"><table class="cw-comp"><thead><tr><th></th>{cabecalho}</tr></thead>'
            f'<tbody>{"".join(linhas)}</tbody></table></div>')


# ------------------------------------------------------------------------- FIPE
def fipe_seletor(prefixo: str, tipo: str = "cars") -> dict | None:
    """Marca, modelo e ano em cascata. Devolve o preço FIPE ou None enquanto faltar escolha."""
    try:
        marcas = fipe.marcas(tipo)
        por_marca = {m["name"]: m["code"] for m in marcas}
        marca = st.selectbox("Marca", sorted(por_marca), index=None, placeholder="Escolha a marca", key=f"{prefixo}_marca")
        if not marca:
            return None

        por_modelo = {m["name"]: m["code"] for m in fipe.modelos(por_marca[marca], tipo)}
        modelo = st.selectbox("Modelo", list(por_modelo), index=None, placeholder="Escolha o modelo", key=f"{prefixo}_modelo")
        if not modelo:
            return None

        opcoes = sorted(fipe.anos(por_marca[marca], por_modelo[modelo], tipo),
                        key=lambda o: fipe.ano_da_opcao(o["code"]), reverse=True)
        por_ano = {o["name"]: o["code"] for o in opcoes}
        ano = st.selectbox("Ano e combustível", list(por_ano), index=None, placeholder="Escolha o ano", key=f"{prefixo}_ano")
        if not ano:
            return None

        dados = fipe.preco(por_marca[marca], por_modelo[modelo], por_ano[ano], tipo)
        dados["marca_id"], dados["modelo_id"] = por_marca[marca], por_modelo[modelo]
        return dados
    except fipe.FipeErro as e:
        st.warning(str(e))
        return None
