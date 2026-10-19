# ADR 0003: Alinhamento de retornos por interseção de datas

- Status: aceito
- Data: 2026-10-19
- Decisores: _preencher com o(s) aluno(s) responsável(is) e commit individual_
- Consultados: SPEC.md
- Informados: Grupo 4

## Contexto e problema
Métricas comparativas e correlação exigem amostra comum. União com NaNs violaria o requisito de DataFrame final sem nulos; imputação foi rejeitada (ADR 0002).

## Critérios de decisão
DataFrame sem NaN/inf; comparabilidade; mensagem clara se não houver interseção.

## Opções consideradas
- Opção A: união com NaN
- Opção B: interseção (inner join) de datas com retorno válido
- Opção C: preencher com zero

## Decisão
Opção B.

## Consequências
- Bom, porque estatísticas usam observação completa por data.
- Ruim, porque ativos com calendários muito distintos encolhem a amostra.
- Gráficos temporais continuam nas séries individuais.

## Confirmação
`align_returns`; `InsufficientDataError` sem interseção; UI de cobertura.

## Prós e contras das opções
### Opção A
- Ruim, porque exige NaN ou imputação.
### Opção B
- Bom, porque cumpre o contrato do barema.
### Opção C
- Ruim, porque zera retornos falsamente.

## Mais informações
SPEC §8.4.
