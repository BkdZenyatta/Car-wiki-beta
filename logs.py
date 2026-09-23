"""Guarda os avisos técnicos (site fora do ar, busca bloqueada, página não abriu) para a
página Admin, em vez de mostrar esse tipo de coisa pra quem só está usando o site.

Fica em memória do processo (não é banco de dados): reinicia quando o app reinicia. Para
um projeto pessoal como esse é suficiente, e evita gastar armazenamento com log técnico.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime

MAXIMO = 300
_registros: deque[dict] = deque(maxlen=MAXIMO)


def registrar(mensagens: list[str], contexto: str = "") -> None:
    """Guarda cada mensagem com hora e contexto (ex.: 'Busca: "civic"'). Ignora lista vazia."""
    agora = datetime.now().strftime("%d/%m %H:%M:%S")
    for msg in mensagens or []:
        _registros.appendleft({"quando": agora, "contexto": contexto, "mensagem": msg})


def listar() -> list[dict]:
    """Mais recente primeiro."""
    return list(_registros)


def limpar() -> None:
    _registros.clear()
