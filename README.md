# Coletor e Processador de Dados de Mercado

Artefato da **Sprint 1 · Grupo 4 · Inteli × BTG Pactual** (Wealth Management / Portfolio Solutions).

**Repo:** https://github.com/Luigi1412/coletor-processador-dados-mercado

Fundação de dados: coleta de preços históricos (yfinance), tratamento conservador, retornos diários alinhados, métricas descritivas, API FastAPI, CLI e interface React.

> **SPEC.md** foi escrito **antes** da implementação.  
> Carteira oficial: `PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA, ABEV3.SA` (`2024-01-02` → `2025-12-31`).  
> Entrega ao professor: [`docs/PARA_O_PROFESSOR.md`](docs/PARA_O_PROFESSOR.md) · Colegas: [`docs/PARA_OS_COLEGAS.md`](docs/PARA_OS_COLEGAS.md)

## Caminho mínimo para o avaliador (obrigatório do barema)

```bash
git clone https://github.com/Luigi1412/coletor-processador-dados-mercado.git
cd coletor-processador-dados-mercado/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -m "not integration" -q
python -m market_data_pipeline.cli collect \
  --tickers PETR4.SA,VALE3.SA,ITUB4.SA,WEGE3.SA,ABEV3.SA \
  --start 2024-01-02 --end 2025-12-31 --output ./output
```

Isso imprime o DataFrame final de retornos (sem NaN), dimensão e período, e grava exports.

## Requisitos

- Python **3.11+**
- Node.js **20+** (só se for subir o frontend)
- Rede para yfinance no demo real (testes unitários rodam offline)

Não há chaves pagas no núcleo.

## Estrutura

```
SPEC.md
README.md
backend/                 # pacote Python + API + CLI + testes
frontend/                # React + TypeScript + Vite (opcional nesta sprint)
config/ativos_oficiais.yaml
docs/                    # metodologia, ADRs, evidências, guia do professor
examples/                # CSVs de exemplo
```

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Testes

```bash
pytest -m "not integration" -q   # sem rede
pytest -m integration -q         # yfinance (rede)
```

### API (opcional)

```bash
uvicorn market_data_pipeline.api:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI: http://127.0.0.1:8000/docs  
Persistência: `backend/data/analyses/<analysis_id>/`

### CLI

```bash
python -m market_data_pipeline.cli defaults
python -m market_data_pipeline.cli collect \
  --tickers PETR4.SA,VALE3.SA,ITUB4.SA,WEGE3.SA,ABEV3.SA \
  --start 2024-01-02 --end 2025-12-31 --output ./output
```

## Frontend (opcional / fora do núcleo do barema)

```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://127.0.0.1:8000
npm install && npm run dev
```

## Limitações

- Dependência do Yahoo Finance (formato, disponibilidade, rate limit).
- Complementos (cotação/fundamentos/notícias) são best-effort e isolados.
- Sem conversão cambial consolidada.
- Excel exportado não substitui automaticamente o artefato de planilha.
- ADRs: cada aluno deve ter commit autoral próprio (ver `docs/PARA_OS_COLEGAS.md`).

## Barema — onde evidenciar

| Critério | Peso | Evidência |
|----------|------|-----------|
| Pipeline | 25% | `compute_daily_returns` · testes · CLI |
| Tratamento | 20% | SPEC/ADR · `quality` · testes de lacuna |
| Relatório | 10% | métricas · `docs/demo/relatorio_oficiais.md` |
| Reprodutibilidade | 10% | este README · deps · config |
| Spec/docs | 15% | `SPEC.md` · metodologia · `docs/evidence/` |
| ADRs | 20% | `docs/adr/` · commits autorais |

## Metodologia

Ver `docs/methodology.md` (versão `1.0.0`).
