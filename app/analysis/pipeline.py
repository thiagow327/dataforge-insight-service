"""Pipeline de análise (código puro — sem IA).

Etapas cobertas na Fase 2:
  1. Validação de qualidade  → ausentes, inválidos, duplicatas
  2. Detecção de anomalias   → valores impossíveis + outliers (IQR)
  4. Estatística             → média, mediana, min, max, desvio, contagens

O enriquecimento (BrasilAPI) e a interpretação por IA entram nas próximas fases.
"""

import math
import re
from typing import Any

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


def analyze(records: list[dict[str, Any]]) -> dict:
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

    return {
        "quality": {
            "total": total,
            "ausentes": ausentes,
            "invalidos": invalidos,
            "duplicatas": duplicatas,
        },
        "statistics": {"valor": valor_stats, "por_produto": por_produto},
        "anomalies": anomalies,
    }
