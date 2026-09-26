from fastapi import APIRouter

from app import schemas
from app.enrichment import enrich_cep

router = APIRouter(tags=["enrichment"])


@router.get("/enrich/{cep}", response_model=schemas.EnrichedCep)
def enrich(cep: str):
    """Enriquece um CEP isolado via BrasilAPI (cidade, estado, região)."""
    return enrich_cep(cep)
