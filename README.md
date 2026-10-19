# Coletor e Processador de Dados de Mercado

Artefato da **Sprint 1 · Grupo 4 · Inteli × BTG Pactual** (Wealth Management / Portfolio Solutions).

Fundação de dados: coleta de preços históricos (yfinance), tratamento conservador, retornos diários alinhados, métricas descritivas, API FastAPI, CLI e interface React.

> **SPEC.md** foi escrito **antes** da implementação.  
> Carteira oficial: `PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA, ABEV3.SA` (`2024-01-02` → `2025-12-31`).  
> Checklist do grupo (remoto, ADRs autorais): [`docs/checklist_grupo.md`](docs/checklist_grupo.md).

## Requisitos

- Python **3.11+**
- Node.js **20+** (frontend)
- Rede para download yfinance (núcleo testável offline com fixtures)

Não há chaves pagas no núcleo.

## Estrutura

```
SPEC.md
README.md
backend/                 # pacote Python + API + CLI + testes
frontend/                # React + TypeScript + Vite
config/tickers.example.yaml
docs/methodology.md
docs/csv_import_model.md
docs/adr/                # MADR + modelo para ADRs autorais
docs/evidence/           # evidências de execução
examples/                # CSVs de exemplo
data/analyses/           # persistência local (gerada em runtime)
```

## Backend (do zero)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Testes

```bash
# Unitários / API com fixtures (sem rede)
pytest -m "not integration" -q

# Integração real yfinance (requer rede)
pytest -m integration -q
```

### API

```bash
cd backend
source .venv/bin/activate
uvicorn market_data_pipeline.api:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI: http://127.0.0.1:8000/docs  
Dados persistidos: `backend/data/analyses/<analysis_id>/`

### CLI (comandos testáveis)

```bash
cd backend
source .venv/bin/activate

# Defaults provisórios
python -m market_data_pipeline.cli defaults

# Coleta com tickers e datas configuráveis (sem editar código)
python -m market_data_pipeline.cli collect \
  --tickers PETR4.SA,VALE3.SA \
  --start 2024-01-01 \
  --end 2025-12-31 \
  --output ./output \
  --allow-partial
```

A CLI imprime prévia do DataFrame, dimensão e período; grava CSV/Excel/Markdown e persiste a análise.

## Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://127.0.0.1:8000
npm install
npm run dev
```

Build de produção:

```bash
npm run build
```

Interface em português, visual institucional (azul-escuro / fundo claro). Identificação discreta de protótipo acadêmico do Grupo 4 — sem logotipo oficial inventado.

## Fluxo principal na UI

1. Selecionar ativos e período (~2 anos sugeridos, editáveis)  
2. Iniciar coleta  
3. Acompanhar processamento  
4. Conferir cobertura/qualidade  
5. Explorar métricas e gráficos  
6. Exportar  
7. Reabrir análises salvas  

## Importação CSV

Modelo: `docs/csv_import_model.md` · exemplos em `examples/`.  
Endpoint: `POST /import/csv`.

## Limitações

- Dependência do Yahoo Finance (formato, disponibilidade, rate limit).
- Complementos (cotação/fundamentos/notícias) são best-effort e isolados.
- Sem conversão cambial consolidada.
- Ativos oficiais do grupo: **pendentes**.
- Excel exportado **não** substitui automaticamente todos os requisitos do artefato de planilha.

## Barema — onde evidenciar

| Critério | Peso | Evidência |
|----------|------|-----------|
| Pipeline | 25% | `compute_daily_returns` · testes · CLI/API |
| Tratamento | 20% | SPEC/ADR · `quality.json` · testes de lacuna |
| Relatório | 10% | métricas · `report.md` |
| Reprodutibilidade | 10% | este README · deps · config exemplo |
| Spec/docs | 15% | `SPEC.md` (pré-código) · metodologia · docstrings |
| ADRs | 20% | `docs/adr/` (MADR) · commits autorais dos alunos |

## Metodologia

Ver `docs/methodology.md` (versão `1.0.0`).
