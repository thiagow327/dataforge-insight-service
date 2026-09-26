"""Interpretação por IA via Ollama.

A IA recebe os NÚMEROS já calculados pelo pipeline e escreve um resumo executivo em
português. Ela não calcula nada — apenas interpreta. Se o Ollama falhar ou demorar,
cai num resumo por template, para o sistema nunca quebrar.
"""

import json

import httpx

from app.config import settings

SYSTEM = (
    "Você é um analista de dados. Escreva um resumo executivo em português do Brasil, "
    "com 3 a 5 frases, claro e objetivo. Interprete SOMENTE os números fornecidos. "
    "NÃO invente dados nem faça cálculos novos. Comente a qualidade dos dados, as "
    "principais estatísticas, as anomalias e a distribuição regional quando houver. "
    "Termine com uma recomendação curta."
)


def _fatos(result: dict) -> dict:
    """Extrai só o que a IA precisa ver, de forma compacta."""
    return {
        "total_registros": result["quality"]["total"],
        "linhas_limpas": result["quality"].get("linhas_limpas"),
        "ausentes": result["quality"]["ausentes"],
        "invalidos": result["quality"]["invalidos"],
        "duplicatas": result["quality"]["duplicatas"],
        "estatisticas_valor": result["statistics"]["valor"],
        "por_produto": result["statistics"]["por_produto"],
        "por_regiao": result["statistics"]["por_regiao"],
        "anomalias": [a["motivo"] for a in result["anomalies"]],
    }


def _prompt(result: dict) -> str:
    fatos = json.dumps(_fatos(result), ensure_ascii=False, indent=2)
    return f"{SYSTEM}\n\nFATOS (JSON):\n{fatos}\n\nResumo executivo:"


def _fallback(result: dict) -> str:
    """Resumo determinístico, usado quando a IA não está disponível."""
    q = result["quality"]
    v = result["statistics"]["valor"]
    regioes = result["statistics"]["por_regiao"]
    partes = [
        f"O conjunto tem {q['total']} registro(s), dos quais {q.get('linhas_limpas', 0)} "
        f"estão totalmente limpos."
    ]
    if q["duplicatas"] or q["invalidos"] or q["ausentes"]:
        partes.append(
            f"Foram encontrados {q['duplicatas']} duplicata(s), "
            f"{sum(q['invalidos'].values())} valor(es) inválido(s) e "
            f"{sum(q['ausentes'].values())} campo(s) ausente(s)."
        )
    if v.get("media") is not None:
        partes.append(f"O valor médio é {v['media']} (mín {v['min']}, máx {v['max']}).")
    if regioes:
        top = max(regioes, key=regioes.get)
        partes.append(f"A região {top} concentra a maior parte dos registros.")
    partes.append("Recomenda-se revisar as linhas problemáticas antes de usar os dados.")
    return " ".join(partes)


def gerar_resumo(result: dict) -> str:
    """Gera o resumo executivo via Ollama, com fallback por template."""
    try:
        resp = httpx.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": _prompt(result),
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        texto = resp.json().get("response", "").strip()
        return texto or _fallback(result)
    except (httpx.HTTPError, ValueError, KeyError):
        return _fallback(result)
