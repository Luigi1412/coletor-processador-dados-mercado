# Mapeamento barema × evidências

| Critério | Peso | Evidências |
|----------|------|------------|
| Pipeline funcional | 25% | `compute_daily_returns` em `pipeline.py`; testes `test_returns_and_metrics.py`; CLI; OpenAPI `/analyses` |
| Tratamento | 20% | SPEC §7–8; ADR 0001–0003; `treatment.py`; `quality.json`; teste de lacuna |
| Relatório | 10% | `reports.py`; métricas; export `relatorio.md`; aba Relatório na UI |
| Reprodutibilidade | 10% | README raiz; `requirements.txt` / `pyproject.toml`; `frontend/package.json`; `.env.example` |
| Spec e docs | 15% | `SPEC.md` (pré-código); `docs/methodology.md`; docstrings; plano de testes no SPEC |
| ADRs individuais | 20% | `docs/adr/` (MADR verificado via gist); template `0000`; alunos devem commitar ADRs próprios |

## Verificações registradas (2026-10-19)

- Unitários: **21 passed** (`pytest -m "not integration"`)
- Integração yfinance: **1 passed** (PETR4.SA, VALE3.SA provisórios); **1 skipped** (ativos oficiais pendentes)
- Frontend: `npm run build` **ok**
- CLI: ver `docs/evidence/cli_demo.txt` (gerado na execução demonstrativa)
