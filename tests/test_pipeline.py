from app.analysis.pipeline import analyze


def fake_enricher(cep: str) -> dict:
    mapa = {
        "01310-100": {"cep": "01310-100", "cidade": "São Paulo", "estado": "SP",
                      "regiao": "Sudeste", "valido": True},
        "20040-002": {"cep": "20040-002", "cidade": "Rio de Janeiro", "estado": "RJ",
                      "regiao": "Sudeste", "valido": True},
        "00000-000": {"cep": "00000-000", "cidade": None, "estado": None,
                      "regiao": None, "valido": False},
    }
    return mapa.get(cep, {"cep": cep, "cidade": None, "estado": None,
                          "regiao": None, "valido": None})


RECORDS = [
    {"data": "2026-03-01", "produto": "Notebook", "cep": "01310-100", "valor": 3299},
    {"data": "2026-03-02", "produto": "Mouse", "cep": "20040-002", "valor": 49},
    {"data": "2026-03-02", "produto": "Notebook", "cep": None, "valor": 3299},
    {"data": "2026-03-03", "produto": "Teclado", "cep": "00000-000", "valor": -150},
    {"data": "2026-03-01", "produto": "Notebook", "cep": "01310-100", "valor": 3299},
]


def test_qualidade_detecta_problemas():
    r = analyze(RECORDS, enricher=fake_enricher)
    q = r["quality"]
    assert q["total"] == 5
    assert q["ausentes"]["cep"] == 1
    assert q["invalidos"]["valor"] == 1
    assert q["invalidos"]["cep"] == 1  # 00000-000 é bem-formado mas inexistente
    assert q["duplicatas"] == 1


def test_anomalias_valor_negativo():
    r = analyze(RECORDS, enricher=fake_enricher)
    motivos = [a["motivo"] for a in r["anomalies"]]
    assert any("negativo" in m for m in motivos)


def test_estatistica_score_e_regiao():
    r = analyze(RECORDS, enricher=fake_enricher)
    assert r["statistics"]["valor"]["media"] == 1959.2
    assert r["statistics"]["por_regiao"]["Sudeste"] == 3
    assert r["quality"]["linhas_limpas"] == 2
    assert r["data_quality_score"] == 0.4


def test_sem_enricher_nao_enriquece():
    r = analyze(RECORDS)  # sem chamadas de rede
    assert r["statistics"]["por_regiao"] == {}
    assert r["enrichment"] == []


def test_dataset_vazio():
    r = analyze([])
    assert r["quality"]["total"] == 0
    assert r["data_quality_score"] == 0.0
