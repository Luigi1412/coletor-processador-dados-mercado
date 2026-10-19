# Registro de escolhas técnicas (implementação)

Complementa o SPEC e os ADRs com justificativas rotineiras tomadas durante a implementação, sem inventar autoria individual de alunos.

1. **Estrutura monorepo** `backend/` + `frontend/` — isolamento claro de runtimes Python e Node.
2. **Typer + Rich na CLI** — UX de terminal legível; mesma biblioteca do núcleo.
3. **Parquet para séries, JSON para metadados** — leitura rápida e inspeção humana dos metadados.
4. **CORS aberto em local** — facilita Vite em :5173 contra API em :8000; restringir em deploy futuro.
5. **Refresh gera nova análise com `parent_analysis_id`** — preserva reprodutibilidade da versão anterior.
6. **Complementos yfinance isolados** — falha retorna payload `available:false`, HTTP 200, sem derrubar o núcleo.
7. **Recharts no frontend** — gráficos com tooltips sem recalcular métricas no browser.
8. **Tipografia IBM Plex + Source Serif 4** — aparência institucional sóbria; azul `#003366` como cor principal.
9. **Sem logo oficial BTG** — apenas identificação textual de protótipo acadêmico do Grupo 4.
10. **Lista provisória de 5 tickers `.SA`** — configurável; marcada como não oficial.
