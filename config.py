"""Sites de origem, estados e campos da ficha técnica.

Para incluir um site novo, basta adicionar uma linha em FONTES.
  papel "anuncios": entra na busca de carros à venda
  papel "ficha":    é lido para montar a ficha técnica do wiki
"""
from __future__ import annotations

from .utils import dominio_de

PRECO_MINIMO = 8000.0  # abaixo disso o "preço" provavelmente é peça, parcela ou outra coisa

FONTES = {
    # anúncios
    "webmotors": {"nome": "Webmotors", "dominio": "webmotors.com.br", "papel": "anuncios", "cor": "#c8102e"},
    "icarros": {"nome": "iCarros", "dominio": "icarros.com.br", "papel": "anuncios", "cor": "#d9480f"},
    "olx": {"nome": "OLX", "dominio": "olx.com.br", "papel": "anuncios", "cor": "#6e0ad6"},
    "usadosbr": {"nome": "UsadosBR", "dominio": "usadosbr.com", "papel": "anuncios", "cor": "#0b57d0"},
    "instacarro": {"nome": "InstaCarro", "dominio": "instacarro.com", "papel": "anuncios", "cor": "#1a7f4b"},
    "autooo": {"nome": "Autooo", "dominio": "autooo.com.br", "papel": "anuncios", "cor": "#0e7490"},
    # fichas técnicas, testes e reviews
    "carrosnaweb": {"nome": "Carros na Web", "dominio": "carrosnaweb.com.br", "papel": "ficha", "cor": "#475569"},
    "quatrorodas": {"nome": "Quatro Rodas", "dominio": "quatrorodas.abril.com.br", "papel": "ficha", "cor": "#b45309"},
    "olhonocarro": {"nome": "Olho no Carro", "dominio": "olhonocarro.com.br", "papel": "ficha", "cor": "#166534"},
    "meucarronovo": {"nome": "MeuCarroNovo", "dominio": "meucarronovo.com.br", "papel": "ficha", "cor": "#7c3aed"},
    "flatout": {"nome": "FlatOut", "dominio": "flatout.com.br", "papel": "ficha", "cor": "#111827"},
}

# A Tabela FIPE oficial (veiculos.fipe.org.br) não tem API pública.
# Os mesmos dados vêm de uma API aberta, em fipe.py.

ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

# (chave, rótulo, unidade, quem é melhor: "max", "min" ou None)
ESPECIFICACOES = [
    ("carroceria", "Carroceria", "", None),
    ("motor", "Motor", "", None),
    ("combustivel", "Combustível", "", None),
    ("potencia_cv", "Potência", "cv", "max"),
    ("torque_kgfm", "Torque", "kgfm", "max"),
    ("cambio", "Câmbio", "", None),
    ("tracao", "Tração", "", None),
    ("aceleracao_0_100_s", "0 a 100 km/h", "s", "min"),
    ("velocidade_maxima_kmh", "Velocidade máxima", "km/h", "max"),
    ("consumo_cidade_kml", "Consumo na cidade", "km/l", "max"),
    ("consumo_estrada_kml", "Consumo na estrada", "km/l", "max"),
    ("comprimento_mm", "Comprimento", "mm", None),
    ("largura_mm", "Largura", "mm", None),
    ("altura_mm", "Altura", "mm", None),
    ("entre_eixos_mm", "Entre-eixos", "mm", "max"),
    ("porta_malas_l", "Porta-malas", "L", "max"),
    ("tanque_l", "Tanque", "L", "max"),
    ("peso_kg", "Peso", "kg", "min"),
    ("portas", "Portas", "", None),
    ("lugares", "Lugares", "", None),
]

CAMPOS_TEXTO = {"carroceria", "motor", "combustivel", "cambio", "tracao"}


def chaves_por_papel(papel: str) -> list[str]:
    return [k for k, f in FONTES.items() if f["papel"] == papel]


def dominio_permitido(url: str) -> bool:
    host = dominio_de(url)
    return any(host == f["dominio"] or host.endswith("." + f["dominio"]) for f in FONTES.values())


def url_da_fonte(url: str, dominio: str) -> bool:
    host = dominio_de(url)
    return host == dominio or host.endswith("." + dominio)
