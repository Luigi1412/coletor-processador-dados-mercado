# Modelo de importação CSV

Arquivo de apoio à integração futura com o artefato de planilha.

## Colunas obrigatórias

| Coluna | Descrição |
|--------|-----------|
| `date` | Data ISO `YYYY-MM-DD` |
| `value` | Número (ponto decimal) |

## Metadados (formulário da API / parâmetros)

| Campo | Valores |
|-------|---------|
| `ticker` | Identificador da série |
| `series_type` | `price` \| `return_index` \| `daily_rate` \| `annualized_rate` |
| `unit` | Ex.: `BRL`, `decimal` |
| `frequency` | Ex.: `daily` |
| `currency` | Ex.: `BRL` |
| `source` | Procedência textual |

## Exemplos

### Preço / cota

```csv
date,value
2024-01-02,100.0
2024-01-03,101.5
2024-01-04,99.2
```

`series_type=price` → retorno \(P_t/P_{t-1}-1\).

### Taxa diária (ex.: CDI diário em decimal)

```csv
date,value
2024-01-02,0.000456
2024-01-03,0.000456
```

`series_type=daily_rate`, `unit=decimal` → valores usados **diretamente** como retorno diário.  
**Não** aplicar variação percentual entre taxas.

### Taxa anualizada

`series_type=annualized_rate` → conversão \((1+r)^{1/252}-1\).

## Limitações

- Não há integração automatizada verificada com API oficial de CDI nesta sprint; use CSV.
- CDI importado **não** substitui um instrumento de renda fixa com marcação a mercado.
