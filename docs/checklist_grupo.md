# Checklist do grupo — fechar Sprint 1 (barema)

Ordem sugerida. A reformulação de UI fica **depois**, em separado.

## 1. Git (repositório do grupo)

- [x] `git init` no workspace local (feito na preparação)
- [ ] Conectar ao remoto do grupo (GitLab/GitHub Inteli), ex.:
  ```bash
  git remote add origin <URL_DO_REPO_DO_GRUPO>
  git push -u origin main
  ```
- [ ] Cada aluno clona/faz pull e configura `user.name` / `user.email` próprios

## 2. Ativos oficiais no SPEC

- [ ] Grupo define a lista definitiva de tickers
- [ ] Preencher `config/ativos_oficiais.yaml` (`definidos: true` + tickers + datas de teste)
- [ ] Atualizar `SPEC.md` §2.3 e §12.3 (remover status “pendente”)
- [ ] (Opcional) alinhar defaults da CLI/UI aos oficiais
- [ ] Rodar teste de integração com esses tickers e salvar evidência em `docs/evidence/`

## 3. ADRs autorais (20% individuais)

- [ ] Cada aluno segue `docs/adr/COMO_REGISTRAR.md`
- [ ] Preencher a tabela de integrantes em `COMO_REGISTRAR.md`
- [ ] Após ativos oficiais: completar “impacto numérico no caso do grupo” nos ADRs

## 4. Depois (fora deste checklist)

- [ ] Reformulação completa da interface (congelar o núcleo até lá)
