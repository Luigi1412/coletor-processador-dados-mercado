# ADRs — Architecture Decision Records

Formato: **MADR** conforme template do módulo ([gist josercf](https://gist.github.com/josercf/fc714afe20773401dc9d56f65174b441)), consultado em 2026-10-19.

**Leia primeiro:** [COMO_REGISTRAR.md](./COMO_REGISTRAR.md) — passo a passo da autoria individual (20% do barema).

## Como usar (autoria individual)

A avaliação de ADRs é **individual pela autoria dos commits**. Cada integrante deve:

1. Copiar `0000-template-madr.md` **ou** assumir um dos `0001`–`0005` com decisão real própria.
2. Preencher **Decisores** com o próprio nome (nunca placeholder).
3. Fazer o **próprio commit** amarrado à decisão.
4. Não inventar nomes, decisões ou commits de colegas.

Os arquivos `0001`–`0005` são **registros técnicos de referência** da implementação. Continuam válidos como documentação do projeto; a nota individual exige commit autoral de cada aluno.

## Índice técnico (referência)

| Arquivo | Tema | Responsável sugerido |
|---------|------|----------------------|
| `0001-preco-ajustado-adj-close.md` | Adj Close vs auto_adjust | Luigi |
| `0002-lacunas-sem-imputacao.md` | Política de lacunas | Hugo |
| `0003-alinhamento-por-intersecao.md` | Interseção de datas | Erik |
| `0004-persistencia-local.md` | Parquet/JSON local | Arthur |
| `0005-fonte-yfinance-e-csv.md` | Provedor e CSV | Enzo |
| `0006-relatorio-descritivo-deterministico.md` | Relatório sem LLM | Rodrigo |

## Impacto numérico

Carteira oficial definida (`definidos: true`). Após `pytest -m integration`, usar `docs/evidence/caso_ativos_oficiais.txt` para completar o impacto numérico em cada ADR no commit autoral.
