# Entrega ao professor — Sprint 1 · Grupo 4

**Repositório:** https://github.com/Luigi1412/coletor-processador-dados-mercado  
**Integrantes:** Luigi, Hugo, Erik, Arthur, Enzo, Rodrigo  
**Parceiro:** BTG Pactual · Portfolio Solutions / Wealth Management

## O que entregar (leitura rápida)

| Item barema | Onde está |
|-------------|-----------|
| Pipeline (25%) | `backend/market_data_pipeline/pipeline.py` · CLI · testes |
| Tratamento (20%) | SPEC §7–8 · ADRs 0001–0003 · `treatment.py` · quality |
| Relatório (10%) | `reports.py` · `docs/demo/relatorio_oficiais.md` |
| Reprodutibilidade (10%) | README (caminho mínimo abaixo) |
| Spec/docs (15%) | `SPEC.md` (pré-código) · metodologia · evidências |
| ADRs individuais (20%) | `docs/adr/` · commits autorais de cada aluno |

## Carteira oficial

`PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `WEGE3.SA`, `ABEV3.SA`  
Período de teste: `2024-01-02` → `2025-12-31`  
Evidência: `docs/evidence/caso_ativos_oficiais.txt` (500×5, cobertura 1.0)

## Caminho mínimo (sem editar código)

```bash
git clone https://github.com/Luigi1412/coletor-processador-dados-mercado.git
cd coletor-processador-dados-mercado/backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Testes determinísticos (sem rede)
pytest -m "not integration" -q

# Demonstração com a carteira oficial
python -m market_data_pipeline.cli collect \
  --tickers PETR4.SA,VALE3.SA,ITUB4.SA,WEGE3.SA,ABEV3.SA \
  --start 2024-01-02 \
  --end 2025-12-31 \
  --output ./output
```

A CLI imprime o DataFrame de retornos, dimensão, período e gera CSV/Excel/Markdown.

OpenAPI (opcional): `uvicorn market_data_pipeline.api:app --port 8000` → http://127.0.0.1:8000/docs

## Decisões de tratamento (resumo)

- Preço: **Adj Close** (`auto_adjust=False`) — evita ajuste duplicado.
- Lacunas: **sem** fill / interpolação / retorno zero; não atravessa lacuna inesperada.
- Alinhamento: **interseção** de datas com retorno válido → DataFrame final sem NaN.

Detalhes: `docs/methodology.md` e ADRs em `docs/adr/`.
