"""Pesquisa nos sites predefinidos.

Como funciona: uma busca com "site:dominio" para cada site escolhido, leitura dos dados
públicos da página (título, foto, JSON-LD) e extração de preço, ano, km, endereço etc.

Cada site pode mudar o HTML ou bloquear robôs. Por isso tudo aqui falha em silêncio,
devolve o que conseguiu e reporta avisos. Nada daqui é garantido para sempre.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import requests
from bs4 import BeautifulSoup

from . import config
from .utils import cached, para_float, url_segura

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CarWikiBot/1.0; pesquisa pessoal)",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
MAX_DETALHAR = 24  # quantas páginas de anúncio abrir por busca
TAMANHO_MAX = 1_500_000

UFS = "|".join(config.ESTADOS)
RE_PRECO = re.compile(r"R\$\s?(\d{1,3}(?:\.\d{3})+|\d{4,7})(?:,\d{2})?")
RE_KM = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)\s?km(?![\w/])", re.I)
RE_ANO = re.compile(r"\b(19[89]\d|20[0-3]\d)(?:\s?/\s?(19[89]\d|20[0-3]\d))?\b")
_PALAVRA = r"[A-ZÀ-Ú][A-Za-zÀ-ÿ'.]*"
RE_LOCAL = re.compile(rf"({_PALAVRA}(?: (?:d[aeo]s?|{_PALAVRA})){{0,2}})\s*[-–/,]\s*({UFS})\b")
NOME_PARA_UF = {nome.lower(): uf for uf, nome in config.ESTADOS.items()}


# --------------------------------------------------------------------------- rede
def fetch(url: str, timeout: int = 6) -> bytes | None:
    """Baixa uma página, só dos sites da lista. Devolve bytes (o BeautifulSoup detecta a codificação)."""
    if not config.dominio_permitido(url):
        return None
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        return None
    if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
        return None
    return r.content[:TAMANHO_MAX]


def _ddg(consulta: str, max_resultados: int) -> tuple[list[dict], str]:
    try:
        try:
            from ddgs import DDGS
        except ImportError:  # nome antigo do pacote
            from duckduckgo_search import DDGS
        with DDGS() as d:
            return list(d.text(consulta, region="br-pt", max_results=max_resultados)), ""
    except Exception as e:  # noqa: BLE001 - a busca não pode derrubar o site
        return [], f"{type(e).__name__}: {e}"


# --------------------------------------------------------------------- extração
def _uf_normalizada(valor: str) -> str:
    v = (valor or "").strip()
    if v.upper() in config.ESTADOS:
        return v.upper()
    return NOME_PARA_UF.get(v.lower(), "")


def extrair_campos(texto: str) -> dict:
    """Tira preço, ano, km, câmbio, combustível e cidade/UF de um texto solto."""
    t = " ".join((texto or "").split())
    preco = 0.0
    for m in RE_PRECO.finditer(t):
        v = para_float(m.group(1))
        if v >= config.PRECO_MINIMO:
            preco = v
            break
    sem_preco = RE_PRECO.sub(" ", t)

    km = None
    m_km = RE_KM.search(sem_preco)
    if m_km:
        km = int(m_km.group(1).replace(".", ""))
    sem_km = RE_KM.sub(" ", sem_preco)

    ano = None
    m_ano = RE_ANO.search(sem_km)
    if m_ano:
        candidato = int(m_ano.group(2) or m_ano.group(1))
        if candidato <= date.today().year + 1:
            ano = candidato

    baixo = t.lower()
    if re.search(r"autom[aá]tic|\baut\b|\bcvt\b|\bdsg\b|tiptronic|dualogic|powershift", baixo):
        cambio = "Automático"
    elif re.search(r"\bmanual\b|\bmec\b", baixo):
        cambio = "Manual"
    else:
        cambio = ""

    combustivel = ""
    for rotulo, padrao in (
        ("Diesel", r"diesel"),
        ("Elétrico", r"el[eé]tric"),
        ("Híbrido", r"h[ií]brid"),
        ("Flex", r"\bflex\b|total flex"),
        ("Gasolina", r"gasolina"),
        ("Etanol", r"etanol|[aá]lcool"),
    ):
        if re.search(padrao, baixo):
            combustivel = rotulo
            break

    cidade = uf = ""
    m_local = RE_LOCAL.search(t)
    if m_local:
        cidade, uf = m_local.group(1), m_local.group(2)

    zero_km = km == 0 or "zero km" in baixo
    return {
        "preco": preco, "ano": ano, "km": km, "cambio": cambio, "combustivel": combustivel,
        "cidade": cidade, "uf": uf, "condicao": "Novo" if zero_km else "Usado",
    }


def _iter_jsonld(soup: BeautifulSoup):
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(tag.string or tag.get_text() or "")
        except ValueError:
            continue
        pilha = [dados]
        while pilha:
            d = pilha.pop()
            if isinstance(d, list):
                pilha.extend(d)
            elif isinstance(d, dict):
                yield d
                if "@graph" in d:
                    pilha.append(d["@graph"])


def _endereco(addr) -> tuple[str, str, str]:
    """(endereço completo, cidade, UF) a partir de um PostalAddress do schema.org."""
    if isinstance(addr, str):
        return addr, "", ""
    if isinstance(addr, dict):
        rua = str(addr.get("streetAddress") or "")
        cidade = str(addr.get("addressLocality") or "")
        uf = _uf_normalizada(str(addr.get("addressRegion") or ""))
        partes = [p for p in (rua, cidade, uf) if p]
        return ", ".join(partes), cidade, uf
    return "", "", ""


def _primeiro(valor):
    if isinstance(valor, list):
        return valor[0] if valor else None
    return valor


# nomes de arquivo típicos de logo/ícone/imagem padrão do site, não do anúncio em si
_IMAGEM_GENERICA = re.compile(
    r"logo|brand|favicon|sprite|placeholder|no[-_]?photo|no[-_]?image|sem[-_]?foto|"
    r"default|share[-_]?image|opengraph|og[-_]?image|social[-_]?card|avatar",
    re.I,
)


def _foto_valida(url) -> str:
    """Aceita a URL só se parecer foto de anúncio, não logo/ícone do site."""
    url = url if isinstance(url, str) else ""
    if url and _IMAGEM_GENERICA.search(url):
        return ""
    return url


def parse_pagina(conteudo) -> dict:
    """Lê foto, preço, endereço e detalhes de uma página de anúncio.

    A foto do JSON-LD (específica do anúncio) tem prioridade sobre a de og:image/twitter:image,
    que em vários sites é o logo da marca e não a foto do carro. Imagens que parecem
    logo/ícone/genéricas são descartadas: é melhor mostrar "sem foto" do que a imagem errada.
    """
    soup = BeautifulSoup(conteudo, "html.parser")
    d = {"thumb": "", "preco": 0.0, "ano": None, "km": None, "endereco": "", "cidade": "",
         "uf": "", "combustivel": "", "cambio": ""}

    for item in _iter_jsonld(soup):
        oferta = _primeiro(item.get("offers"))
        if isinstance(oferta, dict):
            d["preco"] = d["preco"] or para_float(oferta.get("price") or oferta.get("lowPrice") or 0)
            vendedor = oferta.get("seller") if isinstance(oferta.get("seller"), dict) else {}
            local = oferta.get("availableAtOrFrom") if isinstance(oferta.get("availableAtOrFrom"), dict) else {}
            end, cid, uf = _endereco(vendedor.get("address") or local.get("address"))
            d["endereco"] = d["endereco"] or end
            d["cidade"] = d["cidade"] or cid
            d["uf"] = d["uf"] or uf
        if not d["thumb"]:
            img = _primeiro(item.get("image"))
            if isinstance(img, dict):
                img = img.get("url")
            d["thumb"] = _foto_valida(img)
        odometro = item.get("mileageFromOdometer")
        if isinstance(odometro, dict) and d["km"] is None:
            km = para_float(odometro.get("value") or 0)
            d["km"] = int(km) if km else None
        ano = item.get("vehicleModelDate") or item.get("modelDate")
        if ano and d["ano"] is None and str(ano)[:4].isdigit():
            d["ano"] = int(str(ano)[:4])
        d["combustivel"] = d["combustivel"] or str(item.get("fuelType") or "")
        d["cambio"] = d["cambio"] or str(item.get("vehicleTransmission") or "")

    if not d["thumb"]:
        # og:image/twitter:image só entra se a JSON-LD não trouxe nada: em muitos sites
        # essa tag aponta pro logo da marca, não pra foto do anúncio.
        og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if og:
            d["thumb"] = _foto_valida(og.get("content"))

    d["cambio"] = extrair_campos(d["cambio"])["cambio"]
    d["combustivel"] = extrair_campos(d["combustivel"])["combustivel"]

    thumb = d["thumb"]
    if thumb.startswith("//"):
        thumb = "https:" + thumb
    d["thumb"] = url_segura(thumb)
    return d


def texto_limpo(conteudo, limite: int = 6000) -> str:
    soup = BeautifulSoup(conteudo, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())[:limite]


def limpar_titulo(titulo: str) -> str:
    t = re.sub(r"\s*[|\-–—]\s*(Webmotors|iCarros|OLX|UsadosBR|Instacarro|InstaCarro|Autooo)\b.*$", "", titulo or "", flags=re.I)
    return " ".join(t.split())[:140]


def nome_para_ficha(titulo: str) -> str:
    """Título de anúncio vira nome de carro (sem preço, km nem 'usado')."""
    t = RE_PRECO.sub(" ", limpar_titulo(titulo))
    t = RE_KM.sub(" ", t)
    t = re.sub(r"\b(usado|seminovo|novo|à venda|a venda|comprar|zero km)\b", " ", t, flags=re.I)
    t = re.sub(r"\s*[-–|]\s*$", "", " ".join(t.split()))
    return t[:80].strip(" -–|")


def _mesclar(anuncio: dict, extra: dict) -> None:
    """Completa só o que está vazio, para não trocar o dado do resultado da busca."""
    for chave in ("thumb", "endereco", "cidade", "uf", "combustivel", "cambio"):
        if not anuncio.get(chave) and extra.get(chave):
            anuncio[chave] = extra[chave]
    for chave in ("preco", "ano", "km"):
        if not anuncio.get(chave) and extra.get(chave):
            anuncio[chave] = extra[chave]


# ------------------------------------------------------------------ anúncios
@cached(1800)
def buscar_anuncios(termo: str, fontes: tuple, detalhar: bool = True) -> tuple[list[dict], list[str]]:
    """Devolve (anúncios, avisos). Cada anúncio é um dict simples."""
    avisos: list[str] = []
    brutos: list[tuple[str, dict]] = []
    for chave in fontes:
        fonte = config.FONTES[chave]
        resultados, erro = _ddg(f"{termo} site:{fonte['dominio']}", 8)
        if erro:
            avisos.append(f"{fonte['nome']}: a busca falhou ({erro}).")
        for r in resultados:
            url = (r.get("href") or "").split("#")[0]
            if url and config.url_da_fonte(url, fonte["dominio"]):
                brutos.append((chave, r))
        time.sleep(0.4)  # educação com o buscador

    vistos: set[str] = set()
    anuncios: list[dict] = []
    for chave, r in brutos:
        url = (r.get("href") or "").split("#")[0]
        if url in vistos:
            continue
        vistos.add(url)
        fonte = config.FONTES[chave]
        titulo_bruto = r.get("title") or ""
        anuncio = {
            "titulo": limpar_titulo(titulo_bruto), "url": url, "fonte": fonte["nome"], "cor": fonte["cor"],
            "trecho": r.get("body") or "", "thumb": "", "endereco": "",
        }
        anuncio.update(extrair_campos(f"{titulo_bruto} {r.get('body') or ''}"))
        anuncios.append(anuncio)

    if detalhar and anuncios:
        alvo = anuncios[:MAX_DETALHAR]
        with ThreadPoolExecutor(max_workers=6) as pool:
            paginas = list(pool.map(fetch, [a["url"] for a in alvo]))
        sem_acesso = 0
        for anuncio, conteudo in zip(alvo, paginas):
            if not conteudo:
                sem_acesso += 1
                continue
            _mesclar(anuncio, parse_pagina(conteudo))
        if sem_acesso:
            avisos.append(f"{sem_acesso} página(s) não abriram (bloqueio do site ou fora do ar); ficaram sem foto e endereço.")

    for anuncio in anuncios:
        anuncio["tipo"] = "anuncio" if anuncio["preco"] > 0 else "pagina"
    return anuncios, avisos


# -------------------------------------------------------------------- fichas
@cached(86400)
def buscar_fichas(termo: str, max_paginas: int = 5) -> list[dict]:
    """Uma página por site de ficha técnica, com o texto já limpo para a IA ler."""
    achados: list[dict] = []
    for chave in config.chaves_por_papel("ficha"):
        fonte = config.FONTES[chave]
        resultados, _ = _ddg(f"{termo} ficha técnica site:{fonte['dominio']}", 3)
        for r in resultados:
            url = (r.get("href") or "").split("#")[0]
            if url and config.url_da_fonte(url, fonte["dominio"]):
                achados.append({"fonte": fonte["nome"], "titulo": r.get("title") or fonte["nome"],
                                "url": url, "trecho": r.get("body") or ""})
                break
        time.sleep(0.4)
    achados = achados[:max_paginas]
    with ThreadPoolExecutor(max_workers=5) as pool:
        conteudos = list(pool.map(fetch, [a["url"] for a in achados]))
    for pagina, conteudo in zip(achados, conteudos):
        pagina["texto"] = texto_limpo(conteudo) if conteudo else pagina["trecho"]
    return achados
