"""Pipeline de análise (código puro — sem IA).

Etapas cobertas na Fase 2:
  1. Validação de qualidade  → ausentes, inválidos, duplicatas
  2. Detecção de anomalias   → valores impossíveis + outliers (IQR)
  4. Estatística             → média, mediana, min, max, desvio, contagens

O enriquecimento (BrasilAPI) e a interpretação por IA entram nas próximas fases.
"""

import math
import re
from typing import Any, Callable

import pandas as pd

# CEP brasileiro: 8 dígitos, com ou sem hífen (00000-000).
CEP_RE = re.compile(r"^\d{5}-?\d{3}$")


def _num(x: Any) -> float | None:
    """Arredonda para 2 casas, tratando None/NaN."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return round(f, 2)


def analyze(
    records: list[dict[str, Any]],
    enricher: Callable[[str], dict] | None = None,
) -> dict:
    total = len(records)
    df = pd.DataFrame(records, columns=["data", "produto", "cep", "valor"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # ---------- 1. Validação de qualidade ----------
    ausentes = {
        col: int(df[col].isna().sum())
        for col in df.columns
        if int(df[col].isna().sum()) > 0
    }

    duplicatas = int(df.duplicated().sum())

    invalidos: dict[str, int] = {}
    valor_negativos = int((df["valor"] < 0).sum())
    if valor_negativos:
        invalidos["valor"] = valor_negativos

    cep_nonnull = df["cep"].dropna().astype(str)
    cep_malformado = int((~cep_nonnull.str.match(CEP_RE)).sum())
    if cep_malformado:
        invalidos["cep"] = cep_malformado

    # ---------- 2. Detecção de anomalias ----------
    anomalies: list[dict] = []

    # 2a. Valores impossíveis (negativos)
    for pos, valor in enumerate(df["valor"]):
        if pd.notna(valor) and valor < 0:
            anomalies.append(
                {"linha": pos + 1, "campo": "valor", "motivo": f"valor negativo ({_num(valor)})"}
            )

    # 2b. Outliers por IQR (apenas valores válidos e não nulos)
    validos = df.loc[df["valor"].notna() & (df["valor"] >= 0), "valor"]
    if len(validos) >= 4:
        q1, q3 = validos.quantile(0.25), validos.quantile(0.75)
        iqr = q3 - q1
        limite_inf, limite_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        for pos, valor in enumerate(df["valor"]):
            if pd.notna(valor) and valor >= 0 and (valor < limite_inf or valor > limite_sup):
                anomalies.append(
                    {
                        "linha": pos + 1,
                        "campo": "valor",
                        "motivo": f"outlier (fora de [{_num(limite_inf)}, {_num(limite_sup)}])",
                    }
                )

    # ---------- 3. Enriquecimento (BrasilAPI, opcional) ----------
    enrichment: list[dict] = []
    por_regiao: dict[str, int] = {}
    enriquecidos: dict[str, dict] = {}
    if enricher is not None:
        ceps_unicos = df["cep"].dropna().astype(str).unique().tolist()
        enriquecidos = {cep: enricher(cep) for cep in ceps_unicos}
        enrichment = list(enriquecidos.values())

        # CEPs bem-formados mas inexistentes contam como inválidos também
        inexistentes = sum(
            1
            for cep, info in enriquecidos.items()
            if CEP_RE.match(cep) and info.get("valido") is False
        )
        if inexistentes:
            invalidos["cep"] = invalidos.get("cep", 0) + inexistentes

        # Contagem de registros por região (via CEP enriquecido)
        for cep in df["cep"].dropna().astype(str):
            regiao = enriquecidos.get(cep, {}).get("regiao")
            if regiao:
                por_regiao[regiao] = por_regiao.get(regiao, 0) + 1

    # ---------- 4. Estatística ----------
    valores = df["valor"].dropna()
    valor_stats = {
        "count": int(valores.count()),
        "media": _num(valores.mean()) if len(valores) else None,
        "mediana": _num(valores.median()) if len(valores) else None,
        "min": _num(valores.min()) if len(valores) else None,
        "max": _num(valores.max()) if len(valores) else None,
        "desvio_padrao": _num(valores.std()) if len(valores) > 1 else None,
    }
    por_produto = {
        str(k): int(v) for k, v in df["produto"].dropna().value_counts().items()
    }

    # ---------- Score de qualidade: proporção de linhas totalmente limpas ----------
    def _cep_ruim(cep: Any) -> bool:
        if pd.isna(cep):
            return True
        s = str(cep)
        if not CEP_RE.match(s):
            return True
        info = enriquecidos.get(s)
        return bool(info and info.get("valido") is False)

    problema = df[["data", "produto", "cep", "valor"]].isna().any(axis=1)
    problema |= df["valor"] < 0
    problema |= df.duplicated()
    problema |= df["cep"].apply(_cep_ruim)
    linhas_limpas = int((~problema).sum())
    score = round(linhas_limpas / total, 2) if total else 0.0

    return {
        "quality": {
            "total": total,
            "ausentes": ausentes,
            "invalidos": invalidos,
            "duplicatas": duplicatas,
            "linhas_limpas": linhas_limpas,
        },
        "statistics": {
            "valor": valor_stats,
            "por_produto": por_produto,
            "por_regiao": por_regiao,
        },
        "anomalies": anomalies,
        "enrichment": enrichment,
        "data_quality_score": score,
    }
