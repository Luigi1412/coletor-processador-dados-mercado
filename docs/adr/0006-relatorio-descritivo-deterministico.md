# ADR 0006: Relatório descritivo determinístico (sem LLM)

- Status: aceito
- Data: 2026-10-19
- Decisores: Rodrigo _(confirmar com commit individual)_
- Consultados: requisitos do barema (média, desvio, min, max + leitura comparativa)
- Informados: Luigi, Hugo, Erik, Arthur, Enzo

## Contexto e problema
O barema exige leitura comparativa breve entre ativos. Incluir um LLM tornaria o relatório não reproduzível e fora do escopo da sprint (sem chat/LLM).

## Critérios de decisão
Reprodutibilidade, aderência ao barema, simplicidade, ausência de chave paga.

## Opções consideradas
- Opção A: texto gerado por LLM
- Opção B: template determinístico a partir das métricas calculadas
- Opção C: apenas tabela numérica, sem texto

## Decisão
Escolhemos a Opção B: `generate_descriptive_report` monta o Markdown com regras fixas (extremos de média/vol, drawdowns, correlação, limitações), sem classificar “melhor investimento”.

## Consequências
- Bom, porque o mesmo input gera o mesmo texto.
- Ruim, porque o texto é menos “narrativo” que um LLM.
- Impacto numérico no caso do grupo: ver evidência `docs/evidence/caso_ativos_oficiais.txt` — o relatório lista explicitamente maior/menor média e volatilidade dos 5 oficiais na amostra alinhada.
- Predição: esperávamos que a média histórica não fosse apresentada como previsão; o disclaimer fixo garante isso.

## Confirmação
`market_data_pipeline/reports.py`; export `relatorio.md`; teste de exportações; evidência do caso oficial.

## Prós e contras das opções
### Opção A
- Ruim, porque quebra reprodutibilidade e exige integração fora do escopo.
### Opção B
- Bom, porque atende o barema e é testável.
### Opção C
- Ruim, porque o barema pede leitura comparativa.

## Mais informações
Conecta com ADR 0003 (amostra alinhada alimenta as estatísticas do texto).
