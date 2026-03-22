# AGENTS

Repositorio com toolkit Python (`lead_intelligence`) e API FastAPI (`app`).

## Workflows verificados

### Setup de desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Alternativa equivalente:

```bash
pip install -r requirements-dev.txt
```

### Rodar testes

```bash
pytest
pytest tests/test_integration_lead_pipeline.py -v
```

### Subir API localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Comandos de deploy já usados no repo

Procfile/Render start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Docker:

```bash
docker build -t lead-intelligence .
docker run -e OPENAI_API_KEY=sk-... -e PORT=8000 -p 8000:8000 lead-intelligence
```

## Variáveis importantes

- `OPENAI_API_KEY`
- `CORS_ORIGINS`
- `LEADS_FILE`
