# ADR 0002: Política conservadora de lacunas (sem imputação)

- Status: aceito
- Data: 2026-10-19
- Decisores: Hugo _(confirmar com commit individual)_
- Consultados: SPEC.md; requisitos de tratamento do barema
- Informados: Grupo 4

## Contexto e problema
Séries diárias apresentam ausências por feriados, suspensões ou falhas do provedor. Imputar preços fabricaria retornos e distorceria volatilidade.

## Critérios de decisão
Não fabricar cotações; preservar interpretação de retorno diário; transparência no relatório de qualidade.

## Opções consideradas
- Opção A: forward-fill / interpolação
- Opção B: descartar o ativo silenciosamente
- Opção C: não imputar; não atravessar lacuna inesperada; reportar

## Decisão
Escolhemos a Opção C.

## Consequências
- Bom, porque retornos multi-pregão não são rotulados como diários.
- Ruim, porque reduz o tamanho da amostra alinhada.
- Impacto numérico: no caso oficial (5 tickers, 2024–2025), a cobertura pós-alinhamento foi **1,0** com **500** retornos alinhados (`docs/evidence/caso_ativos_oficiais.txt`) — sem fabricar dias; se houvesse forward-fill, n e volatilidade mudariam artificialmente.

## Confirmação
`treatment.compute_valid_daily_returns`; testes `test_gap_does_not_create_multiday_as_daily`.

## Prós e contras das opções
### Opção A
- Ruim, porque inventa preços.
### Opção B
- Ruim, porque oculta falhas ao usuário.
### Opção C
- Bom, porque é auditável e alinhada ao SPEC.

## Mais informações
ADR 0003.
