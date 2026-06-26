![WATTIO](http://wattio.com.br/web/image/1204-212f47c3/Logo%20Wattio.png)

# Backend Wattio

API REST de filmes desenvolvida com `FastAPI`, `SQLAlchemy`, `PostgreSQL`, `Alembic`, `uv` e `Docker`.

## Funcionalidades

- CRUD completo de filmes
- documentacao automatica com FastAPI
- persistencia em PostgreSQL
- migrations com Alembic
- testes unitarios e de integracao
- execucao com `docker compose up --build`

## Rotas

- `GET /health`
- `GET /filmes` com `page` e `page_size`
- `POST /filmes`
- `GET /filmes/{id}`
- `PUT /filmes/{id}` para substituicao completa
- `PATCH /filmes/{id}` para atualizacao parcial
- `DELETE /filmes/{id}`

## Tecnologias

- `Python 3.12`
- `uv`
- `FastAPI`
- `SQLAlchemy 2`
- `PostgreSQL`
- `Alembic`
- `Pytest`
- `HTTPX`
- `Docker`
- `Docker Compose`

## Como executar com Docker

O modo mais simples de subir o projeto e usando Docker:

```bash
docker compose up --build
```

Isso sobe:

- API em `http://localhost:8000`
- Swagger UI em `http://localhost:8000/docs`
- ReDoc em `http://localhost:8000/redoc`
- Healthcheck em `http://localhost:8000/health`

Observacao:

- o container da API executa `alembic upgrade head` automaticamente antes de iniciar o `uvicorn`

## Como executar localmente com uv

### 1. Instalar dependencias

```bash
uv sync --dev
```

### 2. Configurar ambiente

Use o arquivo `.env.example` como referencia.

Exemplo de variaveis:

```env
APP_NAME=Wattio Films API
APP_VERSION=0.1.0
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/wattio
```

### 3. Subir o banco

Se quiser usar somente o PostgreSQL do compose:

```bash
docker compose up db -d
```

### 4. Rodar as migrations

```bash
uv run alembic upgrade head
```

### 5. Iniciar a API

```bash
uv run uvicorn app.main:app --reload
```

## Testes

Executar toda a suite:

```bash
uv run pytest
```

## Migrations

Gerar e aplicar migrations:

```bash
uv run alembic upgrade head
uv run alembic current
```

## Estrutura do projeto

```text
app/
  api/
  core/
  db/
  models/
  repositories/
  schemas/
  services/
tests/
  integration/
  unit/
alembic/
```

## Documentacao da API

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/openapi.json`

## Fluxo sugerido para avaliacao

```bash
docker compose up --build
```

Depois disso, acessar:

- `http://localhost:8000/docs`
- `http://localhost:8000/health`
