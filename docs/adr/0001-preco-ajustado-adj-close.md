# ADR 0001: Uso de Adj Close com auto_adjust desligado

- Status: aceito
- Data: 2026-10-19
- Decisores: Luigi
- Consultados: documentação yfinance; SPEC.md do artefato
- Informados: Hugo, Erik, Arthur, Enzo, Rodrigo

## Contexto e problema
O cálculo de retornos exige preços comparáveis ao longo do tempo na presença de dividendos e splits. O yfinance oferece `Close`, `Adj Close` e a opção `auto_adjust=True`, que reescreve a série OHLCV.

## Critérios de decisão
Evitar ajuste duplicado; clareza da procedência; fidelidade ao retorno total histórico; simplicidade.

## Opções consideradas
- Opção A: `auto_adjust=True` e usar `Close` já ajustado
- Opção B: `auto_adjust=False` e usar explicitamente `Adj Close`
- Opção C: `Close` sem ajuste

## Decisão
Escolhemos a Opção B, porque torna explícito o campo ajustado e impede reaplicar fatores sobre uma série já ajustada.

## Consequências
- Bom, porque a política fica auditável (`price_field` na config/metadados).
- Ruim, porque dependemos da qualidade do Adj Close do Yahoo.
- Impacto numérico no caso do grupo: na amostra oficial alinhada (500 dias, 2024-01-03→2025-12-30), ITUB4.SA teve a maior média diária (~0,103%/dia) e WEGE3.SA a maior volatilidade diária (~1,78%); usar Adj Close evita distorcer esses retornos por eventos corporativos.
- Predição: diferenças maiores em ações com dividendos frequentes (ex.: bancos e utilities).

## Confirmação
`YFinanceProvider` com `auto_adjust=False`; testes de pipeline; `docs/methodology.md`.

## Prós e contras das opções
### Opção A
- Bom, porque simplifica o download.
- Ruim, porque esconde o ajuste e pode confundir com OHLCV “bruto”.
### Opção B
- Bom, porque é explícita e evita duplicidade.
- Neutro, porque mantém dependência do Yahoo.
### Opção C
- Ruim, porque ignora eventos corporativos relevantes para retorno total.

## Mais informações
SPEC §7; ADR 0002.
