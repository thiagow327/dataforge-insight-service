"""Enriquecimento de CEP via BrasilAPI.

Consulta cidade/estado e deriva a região a partir da UF. Resultados são cacheados
em memória para evitar chamadas repetidas à API externa.
"""

import re

import httpx

from app.config import settings

UF_TO_REGIAO: dict[str, str] = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Cache: dígitos do CEP -> resultado do enriquecimento
_cache: dict[str, dict] = {}


def _format_cep(digits: str) -> str:
    return f"{digits[:5]}-{digits[5:]}"


def enrich_cep(cep_raw: str | None) -> dict:
    """Enriquece um CEP. Nunca lança — devolve `valido` False (inexistente/malformado)
    ou None (indeterminado por erro de rede)."""
    digits = re.sub(r"\D", "", cep_raw or "")

    if digits in _cache:
        return _cache[digits]

    base = {"cep": cep_raw, "cidade": None, "estado": None, "regiao": None}

    if len(digits) != 8:
        result = {**base, "valido": False}
        _cache[digits] = result
        return result

    try:
        resp = httpx.get(f"{settings.brasilapi_url}/{digits}", timeout=5.0)
    except httpx.HTTPError:
        # Erro de rede: não cacheia (pode ser transitório) e marca indeterminado.
        return {**base, "cep": _format_cep(digits), "valido": None}

    if resp.status_code == 200:
        data = resp.json()
        estado = data.get("state")
        result = {
            "cep": _format_cep(digits),
            "cidade": data.get("city"),
            "estado": estado,
            "regiao": UF_TO_REGIAO.get(estado),
            "valido": True,
        }
    elif resp.status_code == 404:
        result = {**base, "cep": _format_cep(digits), "valido": False}
    else:
        result = {**base, "cep": _format_cep(digits), "valido": None}

    _cache[digits] = result
    return result
