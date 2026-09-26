# DataForge Insight Service (API Secundária)

API secundária da plataforma **DataForge**. Concentra as regras de negócio: recebe os
registros de um dataset e executa o pipeline de análise:

```
records
   ├─ 1. Validação        → nulos, tipos, duplicatas
   ├─ 2. Anomalias        → outliers (IQR) e valores impossíveis
   ├─ 3. Enriquecimento   → BrasilAPI (CEP → cidade/estado; região pela UF)
   ├─ 4. Estatística      → média, mediana, min, max, contagens
   └─ 5. IA (Ollama)      → resumo executivo em PT-BR a partir dos números
```

> **Regra de ouro:** a IA apenas *interpreta* os números que o código calculou. Ela não
> faz estatística nem inventa correlações.

## Tecnologias

Python 3.12 · FastAPI · pandas · numpy · httpx · Ollama · Docker

## API externa

- **BrasilAPI** — `https://brasilapi.com.br/api/cep/v2/{cep}` — pública e gratuita.

## Como executar

Este serviço é orquestrado pelo `docker-compose.yml` do repositório `dataforge-api`
(clone os dois lado a lado). Para rodar isolado:

```bash
docker build -t dataforge-insight .
docker run -p 8001:8000 --env-file .env dataforge-insight
```

Docs interativas: http://localhost:8001/docs

## Configuração

| Variável | Descrição |
|---|---|
| `OLLAMA_URL` | URL do serviço Ollama |
| `OLLAMA_MODEL` | Modelo de IA (`llama3.2:3b` padrão; `gemma2:2b` alternativa) |
| `BRASILAPI_URL` | URL base da BrasilAPI |

## Status

🚧 Em construção — Fase 0 (setup) concluída. Pipeline de análise nas próximas fases.
