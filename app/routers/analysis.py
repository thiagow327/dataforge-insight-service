from fastapi import APIRouter, HTTPException, status

from app import schemas
from app.analysis.pipeline import analyze
from app.enrichment import enrich_cep
from app.store import LATEST

router = APIRouter(tags=["analysis"])


@router.post("/analysis", response_model=schemas.AnalysisResponse)
def run_analysis(req: schemas.AnalysisRequest):
    """Executa o pipeline de análise (com enriquecimento via BrasilAPI)."""
    records = [r.model_dump() for r in req.records]
    result = analyze(records, enricher=enrich_cep)
    result["dataset_id"] = req.dataset_id
    LATEST[req.dataset_id] = result
    return result


@router.get("/analysis/{dataset_id}", response_model=schemas.AnalysisResponse)
def get_analysis(dataset_id: int):
    """Retorna a última análise calculada para o dataset."""
    if dataset_id not in LATEST:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Nenhuma análise encontrada para este dataset"
        )
    return LATEST[dataset_id]


@router.get("/analysis/{dataset_id}/statistics", response_model=schemas.Statistics)
def get_statistics(dataset_id: int):
    """Retorna apenas as estatísticas da última análise."""
    if dataset_id not in LATEST:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Nenhuma análise encontrada para este dataset"
        )
    return LATEST[dataset_id]["statistics"]
