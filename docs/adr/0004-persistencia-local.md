# ADR 0004: Persistência local Parquet + JSON

- Status: aceito
- Data: 2026-10-19
- Decisores: _preencher com o(s) aluno(s) responsável(is) e commit individual_
- Consultados: requisitos de reabertura e atualização manual
- Informados: Grupo 4

## Contexto e problema
A UI deve reabrir análises e alternar abas sem novo download. Banco de dados adicionaria complexidade desnecessária na sprint 1.

## Critérios de decisão
Reprodutibilidade local; procedência; simplicidade de instalação.

## Opções consideradas
- Opção A: SQLite/PostgreSQL
- Opção B: arquivos locais `data/analyses/<id>/` (Parquet + JSON + MD)
- Opção C: apenas memória de processo

## Decisão
Opção B. Refresh cria nova análise com `parent_analysis_id`, preservando a versão anterior.

## Consequências
- Bom, porque é auditável e portátil.
- Ruim, porque sem índices avançados de busca.
- Confirmação: `persistence.save_analysis` / `load_analysis`; testes de reabertura.

## Prós e contras das opções
### Opção A
- Bom para escala; ruim para onboarding da sprint.
### Opção B
- Bom equilíbrio para entrega acadêmica local.
### Opção C
- Ruim, perde reabertura após restart.

## Mais informações
SPEC §10.
