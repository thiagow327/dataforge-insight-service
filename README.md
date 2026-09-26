# DataForge Insight Service (API Secundária)

API secundária da plataforma **DataForge**. Concentra as regras de negócio: recebe os
registros de um dataset e executa um pipeline de análise de dados, terminando com uma
interpretação por IA.

```
records
   ├─ 1. Validação        → nulos, tipos, duplicatas
   ├─ 2. Anomalias        → outliers (IQR) e valores impossíveis
   ├─ 3. Enriquecimento   → BrasilAPI (CEP → cidade/estado; região pela UF)
   ├─ 4. Estatística      → média, mediana, min, max, contagens, score de qualidade
   └─ 5. IA (Ollama)      → resumo executivo em PT-BR a partir dos números
```

> **Regra de ouro:** a IA apenas *interpreta* os números que o código calculou. Ela não
> faz estatística nem inventa correlações. Se o Ollama estiver indisponível, um resumo por
> template é usado como fallback — o serviço nunca quebra.

## Tecnologias

Python 3.12 · FastAPI · pandas · numpy · httpx · Ollama · Docker

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/analysis` | Roda o pipeline completo sobre os registros recebidos |
| `GET` | `/analysis/{dataset_id}` | Última análise calculada |
| `GET` | `/analysis/{dataset_id}/statistics` | Apenas as estatísticas |
| `GET` | `/enrich/{cep}` | Enriquece um CEP isolado via BrasilAPI |
| `GET` | `/health` | Healthcheck |

### Exemplo

```bash
curl -X POST http://localhost:8001/analysis \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "records": [
        {"data":"2026-03-01","produto":"Notebook","cep":"01310-100","valor":3299},
        {"data":"2026-03-03","produto":"Teclado","cep":"00000-000","valor":-150}
      ]}'
```

```bash
curl http://localhost:8001/enrich/01310-100
# {"cep":"01310-100","cidade":"São Paulo","estado":"SP","regiao":"Sudeste","valido":true}
```

## API externa

- **BrasilAPI** — `GET https://brasilapi.com.br/api/cep/v2/{cep}` — pública, gratuita, sem
  cadastro. Usada para enriquecer os CEPs; a região é derivada da UF em código.

## Como executar

Orquestrado pelo `docker-compose.yml` do repositório `dataforge-api` (clone os dois lado a
lado e rode `docker compose up --build`). Para rodar isolado:

```bash
docker build -t dataforge-insight .
docker run -p 8001:8000 --env-file .env dataforge-insight
```

Docs interativas: http://localhost:8001/docs

## Configuração

| Variável | Descrição | Padrão |
|---|---|---|
| `OLLAMA_URL` | URL do serviço Ollama | `http://ollama:11434` |
| `OLLAMA_MODEL` | Modelo de IA | `llama3.2:3b` (alternativa: `gemma2:2b`) |
| `BRASILAPI_URL` | URL base da BrasilAPI | `https://brasilapi.com.br/api/cep/v2` |

## Testes

```bash
pip install -r requirements.txt pytest
pytest
```

## Estrutura

```
dataforge-insight-service/
├── Dockerfile
├── app/
│   ├── main.py
│   ├── config.py · schemas.py · enrichment.py · llm.py · store.py
│   ├── analysis/pipeline.py
│   └── routers/analysis.py · routers/enrichment.py
└── tests/
```
