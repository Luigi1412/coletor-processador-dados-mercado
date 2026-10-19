# Backend — market_data_pipeline

Pacote Python compartilhado pela API FastAPI e pela CLI.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -m "not integration" -q
uvicorn market_data_pipeline.api:app --reload --port 8000
python -m market_data_pipeline.cli collect -t PETR4.SA,VALE3.SA -s 2024-01-01 -e 2025-12-31 -o ./output
```

Persistência: `data/analyses/<id>/`.
