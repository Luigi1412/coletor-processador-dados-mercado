# ADR 0005: yfinance como provedor núcleo + CSV como extensão

- Status: aceito
- Data: 2026-10-19
- Decisores: _preencher com o(s) aluno(s) responsável(is) e commit individual_
- Consultados: documentação yfinance; requisito de CSV para planilha
- Informados: Grupo 4

## Contexto e problema
Precisamos de download automatizado sem chaves pagas, e de caminho para séries externas (ex.: CDI) sem tratar taxa como preço.

## Critérios de decisão
Sem API paga no núcleo; extensibilidade; diferenciação de unidades.

## Opções consideradas
- Opção A: apenas yfinance
- Opção B: yfinance + importação CSV tipada
- Opção C: integração oficial CDI sem verificação documental completa

## Decisão
Opção B. Integrações oficiais adicionais só quando verificáveis; enquanto isso, CSV documentado.

## Consequências
- Bom, porque o núcleo funciona offline nos testes com fixtures e online via Yahoo.
- Ruim, porque yfinance pode falhar ou mudar formato (mitigado por normalização + retentativas).
- Complementos (cotação/fundamentos/notícias) isolados.

## Confirmação
`providers/`; `docs/csv_import_model.md`; testes de unidade CSV.

## Prós e contras das opções
### Opção A
- Insuficiente para RF/taxas.
### Opção B
- Atende SPEC §6.
### Opção C
- Ruim: não verificar documentação oficial.

## Mais informações
SPEC §6 e §11.
