# Como registrar ADR autoral (obrigatório para os 20% individuais)

Formato: [MADR do módulo](https://gist.github.com/josercf/fc714afe20773401dc9d56f65174b441).

A nota é individual pela **autoria do commit git**. Não peça a outra pessoa para commitar o seu ADR.

## Passo a passo (cada aluno)

1. Configure seu git local com **seu** nome e e-mail acadêmicos (uma vez na máquina):
   ```bash
   git config user.name "Seu Nome Completo"
   git config user.email "seu.email@sou.inteli.edu.br"
   ```
2. Escolha **uma** decisão que você tomou ou defendeu de verdade nesta sprint.
   Temas já documentados como referência técnica (podem ser “assumidos” por um aluno que de fato trabalhou neles):
   - `0001` — Adj Close / preço ajustado
   - `0002` — lacunas sem imputação
   - `0003` — alinhamento por interseção
   - `0004` — persistência local
   - `0005` — yfinance + CSV
   Ou crie um novo arquivo `0006-...md` a partir de `0000-template-madr.md`.
3. Edite o ADR escolhido:
   - Preencha **Decisores** com o seu nome
   - Preencha Consultados / Informados
   - Complete **Impacto numérico no caso do grupo** depois que `config/ativos_oficiais.yaml` estiver definido
4. Faça uma mudança mínima amarrada (ex.: docstring, teste, trecho de docs) **se** o ADR ainda não refletir commit seu no código.
5. Commit **só com a sua identidade**:
   ```bash
   git add docs/adr/NNNN-seu-arquivo.md
   # e arquivos de código relacionados, se houver
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
- Não deixar `Decisores: _preencher..._`.

## Checklist rápido do grupo

| Integrante | ADR (arquivo) | Commit próprio? | Impacto numérico com ativos oficiais? |
|------------|---------------|-----------------|----------------------------------------|
| (nome)     |               |                 |                                        |
| (nome)     |               |                 |                                        |
| (nome)     |               |                 |                                        |
| (nome)     |               |                 |                                        |
