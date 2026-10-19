# Como registrar ADR autoral (obrigatório para os 20% individuais)

Formato: [MADR do módulo](https://gist.github.com/josercf/fc714afe20773401dc9d56f65174b441).

A nota é individual pela **autoria do commit git**. Não peça a outra pessoa para commitar o seu ADR.

## Integrantes e atribuição sugerida

| Integrante | ADR sugerido | Tema | Commit próprio? |
|------------|--------------|------|-----------------|
| Luigi | `0001-preco-ajustado-adj-close.md` | Adj Close | pendente |
| Hugo | `0002-lacunas-sem-imputacao.md` | Lacunas | pendente |
| Erik | `0003-alinhamento-por-intersecao.md` | Interseção | pendente |
| Arthur | `0004-persistencia-local.md` | Persistência | pendente |
| Enzo | `0005-fonte-yfinance-e-csv.md` | yfinance + CSV | pendente |
| Rodrigo | `0006-relatorio-descritivo-deterministico.md` | Relatório | pendente |

A atribuição é organizacional. Cada um deve **assumir de fato** a decisão (editar Decisores, impacto numérico, e commit com a própria identidade).

## Passo a passo (cada aluno)

1. Configure seu git local com **seu** nome e e-mail acadêmicos:
   ```bash
   git config user.name "Seu Nome Completo"
   git config user.email "seu.email@sou.inteli.edu.br"
   ```
2. Abra o ADR da tabela acima (ou crie outro a partir de `0000-template-madr.md` se trocarem entre si).
3. Remova o texto `_(confirmar com commit individual)_` e deixe só o seu nome em **Decisores**.
4. Complete **Impacto numérico no caso do grupo** com base em `docs/evidence/caso_ativos_oficiais.txt`.
5. Commit **só com a sua identidade**:
   ```bash
   git add docs/adr/NNNN-seu-arquivo.md
   git commit -m "$(cat <<'EOF'
   docs(adr): registra decisão sobre <tema curto>

   EOF
   )"
   ```
6. Confira: `git log -1 --format='%an %ae %s'` deve mostrar **seu** nome.

## O que não fazer

- Não inventar decisão que você não tomou.
- Não commitar ADR de colega.
- Não usar `--author` de outra pessoa.
- Não deixar Decisores genéricos.

## Remoto

O repositório ainda será revisado/publicado pelo colega do grupo. Quando houver URL GitLab/GitHub:

```bash
git remote add origin <URL>
git push -u origin main
```
