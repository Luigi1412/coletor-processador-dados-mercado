# Relatório descritivo de retornos diários

Este texto é uma leitura estatística dos resultados calculados. **Não constitui recomendação de investimento.** A média histórica é uma estimativa do retorno esperado diário com base no passado, sem garantia de recorrência futura.

## Médias diárias (estimativa histórica)
- Maior média diária: **ITUB4.SA** (0,10%). Menor média diária: **PETR4.SA** (0,03%).
- Interpretação: diferença de médias descreve o histórico alinhado; não identifica o “melhor investimento”.

## Volatilidade (desvio padrão amostral diário, ddof=1)
- Maior volatilidade: **WEGE3.SA** (1,78%). Menor volatilidade: **ITUB4.SA** (1,23%).

## Extremos de retornos diários
- ABEV3.SA: mín -6,47%, máx 5,50%, n=500, acumulado 14,65%, max drawdown -20,83%
- ITUB4.SA: mín -4,62%, máx 5,41%, n=500, acumulado 61,46%, max drawdown -18,90%
- PETR4.SA: mín -9,14%, máx 7,26%, n=500, acumulado 11,33%, max drawdown -21,06%
- VALE3.SA: mín -5,48%, máx 6,01%, n=500, acumulado 15,49%, max drawdown -27,13%
- WEGE3.SA: mín -11,55%, máx 10,47%, n=500, acumulado 42,42%, max drawdown -38,19%

## Relações lineares (correlação de Pearson)
- |corr| relevante: ITUB4,SA × ABEV3,SA = 0,335
- |corr| relevante: PETR4,SA × VALE3,SA = 0,194
- |corr| relevante: VALE3,SA × ITUB4,SA = 0,182

## Limitações de cobertura e comparabilidade
- Período solicitado: 2024-01-02 a 2025-12-31; efetivo: 2024-01-03 a 2025-12-30.
- Observações alinhadas: 500. Cobertura pós-alinhamento: 1.0.
- Gráficos temporais usam séries individuais válidas; estatísticas comparativas usam a amostra comum alinhada.
- Política: auto_adjust=False e campo Adj Close — evita ajuste duplicado.
- Intervalo solicitado inclusivo: 2024-01-02 a 2025-12-31.
- Retornos calculados antes do alinhamento; DataFrame final = interseção de datas comuns.
- Preço utilizado: Adj Close (ajustado; auto_adjust desligado para evitar ajuste duplicado).

_Fonte: yfinance. Coleta: 2026-10-19T16:04:31Z. Metodologia: 1.0.0._