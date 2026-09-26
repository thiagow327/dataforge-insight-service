from fastapi import FastAPI

from app.routers import analysis, enrichment

app = FastAPI(
    title="DataForge Insight Service",
    description="API secundária: validação, estatística, detecção de anomalias, "
    "enriquecimento via BrasilAPI e interpretação por IA (Ollama).",
    version="0.1.0",
)

app.include_router(analysis.router)
app.include_router(enrichment.router)


@app.get("/health", tags=["infra"])
def health():
    """Healthcheck simples para orquestração e testes."""
    return {"status": "ok", "service": "dataforge-insight-service"}


@app.get("/", tags=["infra"])
def root():
    return {"service": "dataforge-insight-service", "docs": "/docs"}
