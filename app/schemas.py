from datetime import date

from pydantic import BaseModel, Field


# ---------- Entrada ----------
class RecordIn(BaseModel):
    data: date | None = None
    produto: str | None = None
    cep: str | None = None
    valor: float | None = None


class AnalysisRequest(BaseModel):
    dataset_id: int
    records: list[RecordIn] = Field(default_factory=list)


# ---------- Saída ----------
class QualityReport(BaseModel):
    total: int
    ausentes: dict[str, int]
    invalidos: dict[str, int]
    duplicatas: int


class ValorStats(BaseModel):
    count: int
    media: float | None
    mediana: float | None
    min: float | None
    max: float | None
    desvio_padrao: float | None


class Statistics(BaseModel):
    valor: ValorStats
    por_produto: dict[str, int]


class Anomaly(BaseModel):
    linha: int
    campo: str
    motivo: str


class AnalysisResponse(BaseModel):
    dataset_id: int
    quality: QualityReport
    statistics: Statistics
    anomalies: list[Anomaly]
