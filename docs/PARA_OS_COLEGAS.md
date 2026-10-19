# Para os colegas (Hugo, Erik, Arthur, Enzo, Rodrigo)

Repo público: https://github.com/Luigi1412/coletor-processador-dados-mercado

## 1. Clonar e configurar sua identidade

```bash
git clone https://github.com/Luigi1412/coletor-processador-dados-mercado.git
cd coletor-processador-dados-mercado

git config user.name "Seu Nome Completo"
git config user.email "seu.email@sou.inteli.edu.br"
```

## 2. Seu ADR (vale 20% individual)

| Quem | Arquivo |
|------|---------|
| Hugo | `docs/adr/0002-lacunas-sem-imputacao.md` |
| Erik | `docs/adr/0003-alinhamento-por-intersecao.md` |
| Arthur | `docs/adr/0004-persistencia-local.md` |
| Enzo | `docs/adr/0005-fonte-yfinance-e-csv.md` |
| Rodrigo | `docs/adr/0006-relatorio-descritivo-deterministico.md` |
| Luigi | `docs/adr/0001-...` (já confirmado no repo) |

Passos:

1. Abra seu arquivo ADR.
2. Em **Decisores**, deixe só o seu nome (remova `_(confirmar com commit individual)_`).
3. Revise o impacto numérico (já há números oficiais; ajuste se quiser).
4. Commit e push **com a sua conta**:

```bash
git pull
git add docs/adr/000N-seu-arquivo.md
git commit -m "docs(adr): confirma decisão — SeuNome"
git push
```

Se o push for rejeitado por permissão, peçam ao Luigi para adicionar vocês como collaborators, ou abram um PR/fork.

Guia completo: `docs/adr/COMO_REGISTRAR.md`.

## 3. Não precisam mexer agora

- Reformulação da UI (depois)
- Lógica do pipeline (já funcional)
