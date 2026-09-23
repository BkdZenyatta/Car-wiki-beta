"""Tabela FIPE.

O site oficial (veiculos.fipe.org.br) não oferece API pública. Aqui usamos a API aberta
https://fipe.parallelum.com.br, que publica os mesmos dados. Sem token o limite é de
500 consultas por dia; com um token gratuito (FIPE_TOKEN nos Secrets) o limite sobe.
Tudo é guardado em cache por horas para gastar poucas consultas.
"""
from __future__ import annotations

import requests

from .utils import cached, get_secret, para_float

BASE = "https://fipe.parallelum.com.br/api/v2"


class FipeErro(Exception):
    """Erro com mensagem já pronta para mostrar ao usuário."""


def _get(caminho: str):
    headers = {"Accept": "application/json"}
    token = get_secret("FIPE_TOKEN")
    if token:
        headers["X-Subscription-Token"] = str(token)
    try:
        r = requests.get(f"{BASE}{caminho}", headers=headers, timeout=12)
    except requests.RequestException as e:
        raise FipeErro("Não consegui falar com a API da FIPE. Tente de novo em instantes.") from e
    if r.status_code == 429:
        raise FipeErro("O limite diário da API FIPE acabou. Cadastre um token gratuito (FIPE_TOKEN) ou tente amanhã.")
    if r.status_code != 200:
        raise FipeErro(f"A API da FIPE respondeu com erro {r.status_code}.")
    try:
        return r.json()
    except ValueError as e:
        raise FipeErro("A API da FIPE devolveu uma resposta inválida.") from e


@cached(86400)
def marcas(tipo: str = "cars") -> list[dict]:
    return _get(f"/{tipo}/brands")


@cached(86400)
def modelos(marca: str, tipo: str = "cars") -> list[dict]:
    return _get(f"/{tipo}/brands/{marca}/models")


@cached(86400)
def anos(marca: str, modelo: str, tipo: str = "cars") -> list[dict]:
    return _get(f"/{tipo}/brands/{marca}/models/{modelo}/years")


@cached(21600)
def preco(marca: str, modelo: str, ano: str, tipo: str = "cars") -> dict:
    d = _get(f"/{tipo}/brands/{marca}/models/{modelo}/years/{ano}")
    return {
        "marca": d.get("brand", ""),
        "modelo": d.get("model", ""),
        "ano": d.get("modelYear"),
        "combustivel": d.get("fuel", ""),
        "codigo_fipe": d.get("codeFipe", ""),
        "mes": d.get("referenceMonth", ""),
        "preco_txt": d.get("price", ""),
        "preco": para_float(d.get("price", "")),
    }


def ano_da_opcao(codigo: str) -> int:
    """'2019-1' vira 2019. O código 32000 significa zero km."""
    try:
        return int(str(codigo).split("-")[0])
    except ValueError:
        return 0


def rotulo_ano(codigo: str) -> str:
    a = ano_da_opcao(codigo)
    return "0 km" if a >= 32000 else str(a)


def precos_por_ano(marca: str, modelo: str, tipo: str = "cars") -> list[dict]:
    """Uma consulta por ano do modelo. Usa mais da cota da API."""
    saida = []
    for op in sorted(anos(marca, modelo, tipo), key=lambda o: ano_da_opcao(o["code"])):
        p = preco(marca, modelo, op["code"], tipo)
        saida.append({"ano": rotulo_ano(op["code"]), "combustivel": p["combustivel"], "preco": p["preco"]})
    return saida
