# Metodologia — retornos diários e métricas

**Versão:** 1.0.0  
**Artefato:** Coletor e Processador de Dados de Mercado  
**Grupo 4 · Inteli × BTG Pactual**

## 1. Preço utilizado

Campo **Adj Close** do Yahoo Finance (`yfinance`), com `auto_adjust=False`.

- Adj Close já incorpora dividendos e splits na série histórica.
- Evita ajuste duplicado (não reaplicamos fatores sobre Close).
- Configuração explícita: `PipelineConfig.price_field = "Adj Close"`.

## 2. Retorno diário

\[
r_t = \frac{P_t}{P_{t-1}} - 1
\]

Representação interna: **decimal** (0,01 = 1%). A interface exibe percentuais em pt-BR.

## 3. Lacunas e consecutividade

1. Remover duplicatas de data (mantém a última cotação do dia) e ordenar.
2. Construir calendário aproximado = união das datas com cotação no lote.
3. Se há pregão de peers entre duas cotações do ativo → **lacuna inesperada**: o par não gera retorno “diário”.
4. Sem calendário suficiente e gap &gt; 5 dias corridos → causa **indeterminada**; o par também não gera retorno diário.
5. Fins de semana / feriados sem peers → ausência de calendário (informativa).

**Não fazemos:** fill, interpolação, retorno zero, exclusão silenciosa de ativo.

## 4. Alinhamento

Retornos válidos são calculados **por ativo antes** do alinhamento. O DataFrame final é a **interseção** das datas com retorno válido em todos os ativos mantidos. Sem NaN/infinitos. Sem interseção → erro explicativo (nunca tabela vazia como sucesso).

## 5. Métricas

| Métrica | Definição |
|---------|-----------|
| Média | Média aritmética dos retornos alinhados — estimativa histórica do retorno esperado diário (**não** previsão) |
| Desvio | Amostral, `ddof=1` |
| Min / Max | Extremos da amostra alinhada |
| Acumulado | \(\prod(1+r_i)-1\) |
| Drawdown | Sobre riqueza \(W_0=1\), \(W_t=W_{t-1}(1+r_t)\); \(DD_t=W_t/\max_{s\le t}W_s - 1\) |
| Correlação | Pearson; série constante ou n&lt;2 → **não definido** (não zero inventado) |

## 6. Gráficos vs. estatísticas

- Gráficos temporais: séries individuais válidas; `connectNulls=false`.
- Estatísticas comparativas e correlação: amostra comum alinhada.

## 7. Fontes CSV

Tipos: `price`, `return_index`, `daily_rate`, `annualized_rate`. Taxas CDI **não** recebem variação percentual de preço e **não** são apresentadas como preço de ativo nem como RF com marcação a mercado.

## 8. Complementos

Cotação, fundamentos e notícias via yfinance são best-effort e isolados. Não anunciam tempo real garantido.
