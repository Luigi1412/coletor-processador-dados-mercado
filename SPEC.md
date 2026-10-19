# SPEC — Coletor e Processador de Dados de Mercado

**Projeto:** Wealth Management / Portfolio Solutions — Inteli × BTG Pactual  
**Grupo:** 4 — Sprint 1  
**Artefato:** Coletor e Processador de Dados de Mercado  
**Entrega:** 23 de outubro de 2026  
**Status:** Especificação anterior à implementação  
**Versão da metodologia:** `1.0.0`

---

## 1. Problema e objetivo

O módulo de Portfolio Solutions necessitará construir e otimizar carteiras com interação por IA. Antes disso, é obrigatório um alicerce de dados confiável: preços históricos ajustados, retornos diários alinhados e métricas descritivas reproduzíveis.

Esta entrega resolve a fundação de dados:

1. Coletar preços históricos de ativos via provedor automatizado (yfinance) e fontes externas (CSV).
2. Tratar lacunas, duplicidades e falhas parciais de forma conservadora e auditável.
3. Produzir um `DataFrame` Pandas de retornos diários sem NaN/infinitos, com índice de datas consistente.
4. Expor a mesma lógica via biblioteca Python, CLI e API FastAPI, consumida por uma interface React.
5. Persistir análises localmente para reabertura e atualização manual sem recalcular silenciosamente.

**Usuário principal desta versão:** membros do grupo e analista/alocador explorando dados de mercado.

---

## 2. Escopo e limites

### 2.1 No escopo (Sprint 1)

| Área | Entrega |
|------|---------|
| Pipeline | Download yfinance, preços ajustados, retornos simples diários, alinhamento por interseção |
| Tratamento | Política conservadora de lacunas; relatório de qualidade |
| Métricas | Média, desvio amostral (ddof=1), min, max, n, retorno acumulado, drawdown |
| Análises | Correlação, gráficos de preços, base 100, drawdown, dispersão vol×média |
| Relatório | Síntese descritiva determinística em português |
| Backend | FastAPI com OpenAPI, persistência local |
| Frontend | React + TypeScript + Vite, UI em português, visual institucional |
| CLI | Script executável compartilhando o núcleo |
| CSV externo | Importação validada (preços, índice de retorno, taxa diária, taxa anualizada) |
| Complementos | Cotação, fundamentos e notícias isolados (não bloqueiam o núcleo) |
| Exportações | CSV, Excel multiaba, Markdown |
| Docs | SPEC, README, metodologia, ADRs (estrutura + modelo autoral) |
| Testes | Unitários determinísticos + integração real documentada |

### 2.2 Fora de escopo (próximas sprints)

- Login / autenticação
- Chat ou integração com LLM
- Perfil personalizado de investidor
- Otimização de pesos / fronteira eficiente
- Previsão de preços
- Operações reais
- Notebook Jupyter
- Sharpe Ratio e métricas que exijam taxa livre de risco ou outras premissas extras
- Conversão cambial consolidada (apenas sinalização quando moedas diferirem)

### 2.3 Ativos: oficiais vs provisórios

#### Oficiais do grupo (obrigatório para o caso do barema)

Fonte de verdade: [`config/ativos_oficiais.yaml`](config/ativos_oficiais.yaml).

| Campo | Estado atual |
|-------|----------------|
| `definidos` | **`false`** — pendente de decisão do Grupo 4 |
| `tickers` | `[]` (vazio até o grupo preencher) |
| Caso de teste no plano (§12.3) | Bloqueado até `definidos: true` |

Quando o grupo definir a carteira candidata, atualizar o YAML (`definidos: true`, tickers, período de teste) e esta seção do SPEC. Não tratar exemplos provisórios como seleção aprovada.

#### Provisórios (apenas desenvolvimento / demo)

Lista inicial configurável (provisória, **não** aprovada pelo grupo):

```
PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA, WEGE3.SA
```

Período inicial sugerido na UI: ~2 anos até a data corrente; datas editáveis; sem limite estrutural que impeça históricos maiores.

---

## 3. Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + TS + Vite)                               │
│  Seleção → Coleta → Qualidade → Métricas/Gráficos → Export  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/JSON
┌──────────────────────────▼──────────────────────────────────┐
│  API FastAPI                                                │
│  /health, /analyses, /import/csv, /market/*, /export/*      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Núcleo Python (biblioteca compartilhada)                   │
│  providers │ validation │ treatment │ metrics │ reports     │
│  persistence │ exports │ market_extras                      │
└───────┬─────────────────────────────┬───────────────────────┘
        │                             │
   CLI (Typer/argparse)          Persistência local
                                 data/analyses/<id>/
```

**Princípios:**

- Um único caminho de cálculo: biblioteca → CLI e API chamam as mesmas funções.
- Frontend não recalcula métricas financeiras; apenas exibe e formata.
- Complementos de mercado em módulos isolados; falha não interrompe o pipeline histórico.
- Fontes adicionais via interface de provedor, sem acoplamento desnecessário ao yfinance.

---

## 4. Fluxo dos dados

```
Tickers + [start, end]
        │
        ▼
   Validação de entradas
        │
        ▼
   Download por provedor (yfinance / CSV)
        │
        ▼
   Normalização de colunas → preços ajustados (Adj Close)
        │
        ▼
   Auditoria: duplicatas, ordem, lacunas (calendário × inesperadas)
        │
        ▼
   Retornos válidos por ativo (apenas pares consecutivos no calendário aplicável)
        │
        ▼
   Alinhamento por interseção de datas comuns
        │
        ▼
   DataFrame final (sem NaN/inf) + relatório de qualidade + métricas
        │
        ▼
   Persistência + exportações + relatório descritivo
```

---

## 5. Interfaces

### 5.1 Biblioteca Python

```python
def compute_daily_returns(
    tickers: list[str],
    start: str | date,
    end: str | date,
    *,
    provider: str = "yfinance",
    allow_partial: bool = False,
    config: PipelineConfig | None = None,
) -> PipelineResult:
    """
    Retorna PipelineResult contendo:
      - returns: pd.DataFrame  # índice DatetimeIndex, colunas = tickers, sem NaN/inf
      - prices: pd.DataFrame   # preços ajustados das séries individuais válidas
      - quality: QualityReport
      - metrics: dict[str, AssetMetrics]
      - correlation: pd.DataFrame | None  # células NaN = não definido
      - report_md: str
      - metadata: AnalysisMetadata
    Levanta PipelineError em falha total / insuficiência / sem interseção.
    """
```

Funções públicas auxiliares: `compute_metrics`, `compute_correlation`, `compute_drawdown`, `import_external_series`, `generate_descriptive_report`, `export_*`.

### 5.2 CLI

```
python -m market_data_pipeline collect \
  --tickers PETR4.SA,VALE3.SA \
  --start 2024-01-01 \
  --end 2025-12-31 \
  --output ./output/run1 \
  [--allow-partial]
```

Gera CSVs, Excel, Markdown e imprime prévia do DataFrame, dimensão e período.

### 5.3 API (resumo)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Saúde |
| POST | `/analyses` | Criar coleta/análise |
| GET | `/analyses` | Listar análises |
| GET | `/analyses/{id}` | Reabrir análise |
| POST | `/analyses/{id}/refresh` | Atualização (nova versão ou nova análise) |
| GET | `/analyses/{id}/series` | Preços e retornos |
| GET | `/analyses/{id}/metrics` | Métricas e correlação |
| GET | `/analyses/{id}/quality` | Qualidade |
| GET | `/analyses/{id}/report` | Relatório descritivo |
| GET | `/analyses/{id}/export/{fmt}` | csv_prices, csv_returns, csv_metrics, xlsx, md |
| POST | `/import/csv` | Importar série externa |
| GET | `/market/quote/{ticker}` | Última cotação disponível |
| GET | `/market/fundamentals/{ticker}` | Fundamentos |
| GET | `/market/news/{ticker}` | Notícias |
| GET | `/config/defaults` | Tickers provisórios e período sugerido |

---

## 6. Contratos de entrada e saída

### 6.1 Entrada (análise)

```json
{
  "tickers": ["PETR4.SA", "VALE3.SA"],
  "start": "2024-01-01",
  "end": "2025-12-31",
  "allow_partial": false,
  "provider": "yfinance"
}
```

**Validações:**

- `tickers`: lista não vazia; máx. 30 ativos; símbolos não vazios; sem duplicatas (normalização uppercase/strip).
- `start` < `end`; formato ISO `YYYY-MM-DD`.
- Intervalo máximo recomendado: 15 anos (aviso, não bloqueio estrutural rígido além de um teto de segurança de 40 anos).
- Timeout de download: 60 s por lote; até 3 tentativas com backoff.

### 6.2 Saída (núcleo)

- `returns`: `DataFrame[float64]`, índice `DatetimeIndex` ordenado único, colunas = ativos disponíveis na análise final.
- Representação interna: decimal (0.01 = 1%).
- Sem NaN, sem ±inf.
- Erro tipado se tabela vazia / sem interseção — **nunca** sucesso com tabela vazia.

### 6.3 Persistência

Diretório: `data/analyses/<analysis_id>/`

```
metadata.json      # id, params, fonte, collected_at, methodology_version, parent_id?
prices.parquet
returns.parquet
metrics.json
correlation.json
quality.json
report.md
exports/           # gerados sob demanda ou na criação
```

---

## 7. Política de preços ajustados

**Decisão:** usar `Adj Close` do yfinance como preço de trabalho para cálculo de retornos.

**Justificativa:**

- `Adj Close` já incorpora ajustes de dividendos e splits na série histórica do Yahoo Finance.
- Evita aplicar um segundo fator de ajuste sobre `Close` (ajuste duplicado).
- Configuração explícita: `PipelineConfig.price_field = "Adj Close"`; documentado em ADR e metodologia.

**Evitar ajuste duplicado:** não multiplicar `Close` por `Adj Close/Close` nem usar bibliotecas de ajuste adicional sobre a série já ajustada.

---

## 8. Política de dados ausentes e alinhamento

### 8.1 O que NÃO fazer

- Não preencher preços ausentes (forward/back fill).
- Não substituir retornos ausentes por zero.
- Não interpolar cotações.
- Não excluir silenciosamente um ativo solicitado.

### 8.2 Calendário e lacunas

Para cada ativo, após remover duplicatas (manter última observação do dia) e ordenar:

1. Identificar datas negociadas presentes na série.
2. Quando houver calendário de referência do mercado (ex.: união das datas observadas de todos os ativos BR no lote, ou calendário B3 aproximado pela união), classificar:
   - **Ausência em dia sem pregão esperado** → calendário sem negociação (informativo).
   - **Ausência em dia em que peer(s) do mesmo mercado negociaram e o ativo tinha histórico ativo** → lacuna inesperada.
3. Se informação insuficiente → registrar “causa indeterminada”.

### 8.3 Retornos válidos

Retorno simples apenas entre observações **consecutivas no calendário aplicável do ativo** (duas datas de pregão sucessivas na série do ativo, sem lacuna inesperada entre elas):

\[
r_t = \frac{P_t}{P_{t-1}} - 1
\]

Não calcular retorno atravessando lacuna inesperada de preço (evita tratar variação multi-pregão como retorno “diário”).

### 8.4 Alinhamento

Após calcular retornos válidos por ativo, alinhar pela **interseção** das datas com retorno válido em todos os ativos mantidos na análise. Resultado final sem nulos.

Se `allow_partial=true` e alguns tickers falharam no download, analisar apenas os disponíveis **após confirmação explícita** do parâmetro.

### 8.5 Relatório de qualidade (obrigatório)

- Período solicitado vs. efetivo
- Observações por ativo antes/depois
- Lacunas e duplicidades
- Datas removidas no alinhamento
- Ativos indisponíveis
- Impacto do alinhamento na cobertura
- Fonte e horário da coleta (`collected_at` UTC ISO)

---

## 9. Definições e fórmulas das métricas

Seja \(r_1,\ldots,r_n\) a amostra alinhada do ativo.

| Métrica | Fórmula / definição |
|---------|---------------------|
| Média diária | \(\bar{r} = \frac{1}{n}\sum r_i\) — estimativa histórica do retorno esperado diário (**não** previsão) |
| Desvio padrão amostral | \(s = \sqrt{\frac{1}{n-1}\sum (r_i-\bar{r})^2}\), `ddof=1`; indefinido se \(n<2\) |
| Mínimo / Máximo | \(\min r_i\), \(\max r_i\) |
| Observações | \(n\) |
| Retorno acumulado | \(R = \prod_{i=1}^{n}(1+r_i) - 1\) (composição, não soma) |
| Trajetória de riqueza | \(W_0 = 1\), \(W_t = W_{t-1}(1+r_t)\) |
| Drawdown | \(DD_t = \frac{W_t}{\max_{s\le t} W_s} - 1\) |
| Max drawdown | \(\min_t DD_t\) |

**Correlação:** Pearson sobre a amostra alinhada. Se série constante ou \(n<2\) para o par → célula “não definido” (NaN serializado com flag), **nunca** correl = 0 inventado.

**Gráficos temporais:** usar séries individuais válidas; sinalizar interrupções; não conectar artificialmente após remoção de períodos intermediários. Estatísticas comparativas usam a amostra comum.

**Moedas:** se tickers em moedas distintas, sinalizar ausência de conversão; sem consolidação patrimonial.

---

## 10. Persistência e procedência

Cada análise registra:

- `analysis_id` (UUID)
- Parâmetros de entrada
- `source` (yfinance / csv / misto)
- `collected_at`
- `methodology_version`
- `parent_analysis_id` (quando refresh gera nova versão)
- Hashes ou contagens de linhas dos artefatos

Reabrir = ler persistência local, sem novo download. Refresh = nova coleta explícita (nova análise ou versão vinculada).

---

## 11. Fontes adicionais e renda fixa

### 11.1 CSV externo

Modelo documentado em `docs/csv_import_model.md`. Tipos:

| `series_type` | Interpretação | Transformação para retorno diário |
|---------------|---------------|-----------------------------------|
| `price` | Preço/cota | \(P_t/P_{t-1}-1\) |
| `return_index` | Índice de retorno cumulativo | idem sobre o índice |
| `daily_rate` | Taxa diária já em decimal | usar diretamente (não aplicar variação de preço) |
| `annualized_rate` | Taxa anualizada | converter p/ diária conforme convenção documentada (252 úteis padrão BR) |

Sempre registrar: unidade, frequência, moeda, fonte, transformações.

**CDI:** não apresentar como preço de ativo nem como substituto de instrumento de RF com marcação a mercado.

### 11.2 Integrações automatizadas extras

Somente o que for verificável na documentação oficial. Sem integração pronta → CSV permanece utilizável; limitação documentada.

---

## 12. Plano de testes

### 12.1 Unitários (sem rede, fixtures)

| Caso | Esperado |
|------|----------|
| Retornos conhecidos | Bateria manual \(P=[100,110,99]\) → retornos exatos |
| Média, std ddof=1, min, max | Valores calculados à mão |
| Acumulado e drawdown | Trajetória conhecida |
| Lacuna intermediária | Sem fill; sem retorno multi-dia como diário |
| Datas duplicadas/desordenadas | Normalização correta |
| Ticker inválido | Erro claro |
| Falha parcial | Lista de falhas; `allow_partial` |
| Resposta vazia | Erro |
| Intervalo inválido | Erro de validação |
| Amostra insuficiente | Erro |
| Sem interseção | Erro explicativo |
| Série constante × correlação | “não definido” |
| Unidades CSV | Rejeição/conversão correta |
| Formatos yfinance (MultiIndex etc.) | Normalização |

### 12.2 Integração

- CLI ↔ API ↔ exportações consistentes (mesmo núcleo).
- Reabertura de análise salva.
- Teste real yfinance com 2–3 ativos; registrar evidência ou bloqueio de rede.

### 12.3 Caso com os dados do grupo (barema — Spec/docs)

**Status:** pendente enquanto `config/ativos_oficiais.yaml` → `definidos: false`.

Quando definidos, o caso deve:

1. Usar exclusivamente os tickers oficiais do YAML.
2. Rodar coleta no período de teste registrado no YAML.
3. Gerar DataFrame de retornos sem nulos + relatório descritivo.
4. Registrar evidência em `docs/evidence/caso_ativos_oficiais.txt` (shape, período efetivo, `collected_at`).
5. Atualizar o impacto numérico nos ADRs individuais.

---

## 13. Critérios de aceite (barema)

| Critério | Peso | Evidência prevista |
|----------|------|--------------------|
| Pipeline funcional | 25% | `compute_daily_returns` + testes + execução CLI/API |
| Tratamento | 20% | Política em SPEC/ADR + `quality.json` + testes de lacuna |
| Relatório | 10% | Métricas + `report.md` determinístico |
| Reprodutibilidade | 10% | README do zero + `requirements`/`package.json` + config exemplo |
| Spec e docs | 15% | Este SPEC (anterior), plano de testes, README, docstrings |
| ADRs individuais | 20% | `/docs/adr/` no formato MADR + modelo para autoria real dos alunos |

---

## 14. Limites operacionais documentados

| Limite | Valor |
|--------|-------|
| Máx. tickers por análise | 30 |
| Timeout download | 60 s |
| Tentativas | 3 (backoff exponencial) |
| Histórico máximo aceito | 40 anos (segurança) |
| Período UI default | 2 anos |
| Base riqueza drawdown | \(W_0 = 1\) |
| Convenção dias úteis (taxa anual→diária) | 252 |

---

## 15. Escolhas técnicas registradas (pré-implementação)

1. **Adj Close** como preço ajustado único — evita ajuste duplicado.
2. **Interseção de datas** para o DataFrame final — garante ausência de NaN sem imputação.
3. **Retornos antes do alinhamento** — preserva interpretação diária.
4. **Persistência Parquet + JSON** — local, auditável, sem banco obrigatório.
5. **FastAPI + React/Vite** — conforme requisito do artefato.
6. **Typer/argparse CLI** — mesma biblioteca do núcleo.
7. **Sem chaves pagas** no núcleo.
8. **Complementos yfinance** isolados (info, news) — best-effort.

---

*Fim da especificação. A implementação deve aderir a este documento; desvios relevantes geram ADR.*
