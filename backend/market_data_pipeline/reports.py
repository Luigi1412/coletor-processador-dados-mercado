"""Relatório descritivo determinístico em português."""

from __future__ import annotations

from market_data_pipeline.metrics import correlation_undefined_reason
from market_data_pipeline.models import AssetMetrics, QualityReport
import pandas as pd


def _pct(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "n/d"
    return f"{x * 100:.{digits}f}%".replace(".", ",")


def generate_descriptive_report(
    metrics: dict[str, AssetMetrics],
    correlation: pd.DataFrame,
    returns: pd.DataFrame,
    quality: QualityReport,
) -> str:
    """Gera síntese comparativa determinística — descrição estatística, não recomendação."""
    lines: list[str] = []
    lines.append("# Relatório descritivo de retornos diários")
    lines.append("")
    lines.append(
        "Este texto é uma leitura estatística dos resultados calculados. "
        "**Não constitui recomendação de investimento.** "
        "A média histórica é uma estimativa do retorno esperado diário com base no passado, "
        "sem garantia de recorrência futura."
    )
    lines.append("")

    if not metrics:
        lines.append("Sem métricas disponíveis.")
        return "\n".join(lines)

    # Médias
    with_mean = [(t, m.mean_daily) for t, m in metrics.items() if m.mean_daily is not None]
    if with_mean:
        hi = max(with_mean, key=lambda x: x[1])
        lo = min(with_mean, key=lambda x: x[1])
        lines.append("## Médias diárias (estimativa histórica)")
        lines.append(
            f"- Maior média diária: **{hi[0]}** ({_pct(hi[1])}). "
            f"Menor média diária: **{lo[0]}** ({_pct(lo[1])})."
        )
        lines.append(
            "- Interpretação: diferença de médias descreve o histórico alinhado; "
            "não identifica o “melhor investimento”."
        )
        lines.append("")

    # Volatilidade
    with_std = [(t, m.std_daily) for t, m in metrics.items() if m.std_daily is not None]
    if with_std:
        hi = max(with_std, key=lambda x: x[1])
        lo = min(with_std, key=lambda x: x[1])
        lines.append("## Volatilidade (desvio padrão amostral diário, ddof=1)")
        lines.append(
            f"- Maior volatilidade: **{hi[0]}** ({_pct(hi[1])}). "
            f"Menor volatilidade: **{lo[0]}** ({_pct(lo[1])})."
        )
        lines.append("")

    # Extremos
    lines.append("## Extremos de retornos diários")
    for t, m in sorted(metrics.items()):
        lines.append(
            f"- {t}: mín {_pct(m.min_daily)}, máx {_pct(m.max_daily)}, "
            f"n={m.n_observations}, acumulado {_pct(m.cumulative_return)}, "
            f"max drawdown {_pct(m.max_drawdown)}"
        )
    lines.append("")

    # Correlação
    lines.append("## Relações lineares (correlação de Pearson)")
    if correlation is None or correlation.empty:
        lines.append("- Matriz indisponível.")
    else:
        pairs: list[tuple[str, str, float]] = []
        cols = list(correlation.columns)
        for i, a in enumerate(cols):
            for b in cols[i + 1 :]:
                val = correlation.loc[a, b]
                if pd.isna(val):
                    reason = correlation_undefined_reason(returns, a, b) or "não definido"
                    lines.append(f"- {a} × {b}: **não definido** ({reason}).")
                else:
                    pairs.append((a, b, float(val)))
        if pairs:
            pairs_sorted = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
            top = pairs_sorted[:3]
            for a, b, v in top:
                lines.append(f"- |corr| relevante: {a} × {b} = {v:.3f}".replace(".", ","))
    lines.append("")

    # Cobertura
    lines.append("## Limitações de cobertura e comparabilidade")
    lines.append(
        f"- Período solicitado: {quality.requested_start} a {quality.requested_end}; "
        f"efetivo: {quality.effective_start or 'n/d'} a {quality.effective_end or 'n/d'}."
    )
    lines.append(
        f"- Observações alinhadas: {quality.aligned_dates_count}. "
        f"Cobertura pós-alinhamento: "
        f"{quality.alignment_coverage_ratio if quality.alignment_coverage_ratio is not None else 'n/d'}."
    )
    if quality.unavailable_tickers:
        lines.append(f"- Ativos indisponíveis: {', '.join(quality.unavailable_tickers)}.")
    if quality.mixed_currencies:
        lines.append(
            f"- Moedas distintas detectadas ({', '.join(quality.currencies)}): "
            "resultados **não** foram convertidos para uma moeda comum; "
            "não há consolidação patrimonial."
        )
    lines.append(
        "- Gráficos temporais usam séries individuais válidas; estatísticas comparativas "
        "usam a amostra comum alinhada."
    )
    for note in quality.notes:
        lines.append(f"- {note}")
    lines.append("")
    lines.append(f"_Fonte: {quality.source}. Coleta: {quality.collected_at}. Metodologia: {quality.methodology_version}._")
    return "\n".join(lines)
