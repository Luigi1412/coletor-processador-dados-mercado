"""Orquestração do pipeline: validação → download → tratamento → métricas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Sequence

import pandas as pd

from market_data_pipeline.config import METHODOLOGY_VERSION, PipelineConfig
from market_data_pipeline.exceptions import (
    InsufficientDataError,
    PartialFailureError,
    PipelineError,
    ProviderError,
)
from market_data_pipeline.metrics import compute_all_metrics, compute_correlation, drawdown_series
from market_data_pipeline.models import (
    AnalysisMetadata,
    AssetMetrics,
    AssetQuality,
    GapRecord,
    QualityReport,
)
from market_data_pipeline.providers.base import ProviderDownloadResult
from market_data_pipeline.providers.yfinance_provider import YFinanceProvider
from market_data_pipeline.reports import generate_descriptive_report
from market_data_pipeline.treatment import align_returns, build_market_calendar, compute_valid_daily_returns
from market_data_pipeline.validation import validate_request


@dataclass
class PipelineResult:
    """Resultado completo do pipeline. O núcleo efetivamente devolve DataFrame de retornos."""

    returns: pd.DataFrame
    prices: pd.DataFrame  # séries individuais (podem ter datas distintas; NaN onde ausente)
    individual_returns: dict[str, pd.Series]
    drawdowns: dict[str, pd.Series]
    quality: QualityReport
    metrics: dict[str, AssetMetrics]
    correlation: pd.DataFrame
    report_md: str
    metadata: AnalysisMetadata
    extras: dict[str, Any] = field(default_factory=dict)

    def preview(self, n: int = 5) -> str:
        return (
            f"shape={self.returns.shape}, "
            f"período={self.quality.effective_start}→{self.quality.effective_end}\n"
            f"{self.returns.head(n)}"
        )


def _empty_prices_frame(treated_prices: dict[str, pd.Series]) -> pd.DataFrame:
    if not treated_prices:
        return pd.DataFrame()
    return pd.DataFrame(treated_prices).sort_index()


def run_from_provider_result(
    download: ProviderDownloadResult,
    tickers: list[str],
    start: date,
    end: date,
    *,
    allow_partial: bool = False,
    config: PipelineConfig | None = None,
    analysis_id: str | None = None,
    parent_analysis_id: str | None = None,
) -> PipelineResult:
    """Executa tratamento e métricas a partir de um download já obtido (testável sem rede)."""
    import uuid

    cfg = config or PipelineConfig()
    failed = dict(download.failed)
    available = [t for t in tickers if t in download.prices and not download.prices[t].empty]
    unavailable = [t for t in tickers if t not in available]

    for t in unavailable:
        if t not in failed:
            failed[t] = "Ativo indisponível após download."

    if not available:
        raise InsufficientDataError(
            "Nenhum ativo retornou dados utilizáveis no intervalo solicitado.",
            details={"failed": failed, "tickers": tickers},
        )

    if unavailable and not allow_partial:
        raise PartialFailureError(
            "Falha parcial na coleta. Alguns ativos falharam. "
            "Reenvie com allow_partial=true para analisar apenas os disponíveis: "
            f"{', '.join(available)}. Falhos: {', '.join(unavailable)}.",
            failed=unavailable,
            available=available,
        )

    price_map = {t: download.prices[t] for t in available}
    calendar = build_market_calendar(price_map)

    treated_list = []
    all_gaps: list[GapRecord] = []
    for t in available:
        ta = compute_valid_daily_returns(price_map[t], t, market_calendar=calendar)
        ta.quality.currency = download.currencies.get(t)
        treated_list.append(ta)
        all_gaps.extend(ta.gaps)

    # Manter ativos com ao menos 1 retorno válido; o mínimo estrutural
    # (min_observations) aplica-se à amostra alinhada final.
    usable = [t for t in treated_list if t.quality.observations_with_valid_returns >= 1]
    dropped = [t.ticker for t in treated_list if t not in usable]
    for t in dropped:
        failed[t] = "Nenhum retorno diário válido após tratamento de lacunas."
        unavailable.append(t)

    if not usable:
        raise InsufficientDataError(
            "Não há retornos diários válidos suficientes após o tratamento.",
            details={"failed": failed},
        )

    if dropped and not allow_partial and set(dropped) & set(tickers):
        # Se o usuário pediu todos e alguns caíram no tratamento
        still_ok = [t.ticker for t in usable]
        raise PartialFailureError(
            "Após o tratamento, parte dos ativos ficou sem amostra válida. "
            f"Disponíveis: {', '.join(still_ok)}. "
            "Reenvie com allow_partial=true para continuar apenas com estes.",
            failed=sorted(set(unavailable)),
            available=still_ok,
        )

    aligned, removed_dates, coverage = align_returns(usable, min_observations=cfg.min_observations)
    if aligned.empty:
        raise InsufficientDataError(
            "Não há interseção válida de datas de retorno entre os ativos. "
            "Ajuste o período, remova ativos com cobertura incompatível ou use allow_partial.",
            details={
                "available": [t.ticker for t in usable],
                "dates_removed": removed_dates[:50],
            },
        )

    # Preços individuais (outer join — NaN sinaliza ausência; gráficos devem tratar interrupções)
    prices_df = _empty_prices_frame({t.ticker: t.prices for t in usable})
    individual_returns = {t.ticker: t.valid_returns for t in usable}
    drawdowns = {
        t.ticker: drawdown_series(aligned[t.ticker], base=cfg.wealth_base) for t in usable if t.ticker in aligned.columns
    }

    currencies = sorted({c for c in download.currencies.values() if c})
    mixed = len(set(currencies)) > 1

    assets_quality = []
    for t in usable:
        assets_quality.append(t.quality)
    for t in sorted(set(unavailable)):
        assets_quality.append(
            AssetQuality(
                ticker=t,
                observations_raw=0,
                observations_after_dedup=0,
                observations_with_valid_returns=0,
                observations_aligned=0,
                duplicates_removed=0,
                available=False,
                failure_reason=failed.get(t, "indisponível"),
            )
        )

    notes = list(download.raw_notes)
    notes.append(
        "Retornos calculados antes do alinhamento; DataFrame final = interseção de datas comuns."
    )
    notes.append(
        f"Preço utilizado: {cfg.price_field} (ajustado; auto_adjust desligado para evitar ajuste duplicado)."
    )
    if mixed:
        notes.append("Moedas distintas — sem conversão cambial.")

    effective_start = aligned.index.min().date().isoformat()
    effective_end = aligned.index.max().date().isoformat()

    quality = QualityReport(
        requested_start=start.isoformat(),
        requested_end=end.isoformat(),
        effective_start=effective_start,
        effective_end=effective_end,
        requested_tickers=list(tickers),
        available_tickers=[t.ticker for t in usable],
        unavailable_tickers=sorted(set(unavailable)),
        aligned_dates_count=len(aligned),
        dates_removed_by_alignment=removed_dates,
        alignment_coverage_ratio=coverage,
        gaps=all_gaps,
        assets=assets_quality,
        source=download.source,
        collected_at=download.collected_at,
        methodology_version=METHODOLOGY_VERSION,
        notes=notes,
        currencies=currencies,
        mixed_currencies=mixed,
    )

    metrics = compute_all_metrics(aligned, wealth_base=cfg.wealth_base)
    corr = compute_correlation(aligned)
    report_md = generate_descriptive_report(metrics, corr, aligned, quality)

    aid = analysis_id or str(uuid.uuid4())
    metadata = AnalysisMetadata(
        analysis_id=aid,
        tickers=list(tickers),
        start=start.isoformat(),
        end=end.isoformat(),
        allow_partial=allow_partial,
        provider=download.source,
        source=download.source,
        collected_at=download.collected_at,
        methodology_version=METHODOLOGY_VERSION,
        parent_analysis_id=parent_analysis_id,
        price_field=cfg.price_field,
    )

    return PipelineResult(
        returns=aligned,
        prices=prices_df,
        individual_returns=individual_returns,
        drawdowns=drawdowns,
        quality=quality,
        metrics=metrics,
        correlation=corr,
        report_md=report_md,
        metadata=metadata,
    )


def compute_daily_returns(
    tickers: Sequence[str],
    start: str | date,
    end: str | date,
    *,
    provider: str = "yfinance",
    allow_partial: bool = False,
    config: PipelineConfig | None = None,
    download_result: ProviderDownloadResult | None = None,
    analysis_id: str | None = None,
    parent_analysis_id: str | None = None,
) -> PipelineResult:
    """Função pública: tickers + intervalo → DataFrame de retornos diários (via PipelineResult.returns).

    Parameters
    ----------
    tickers :
        Lista de símbolos (ex.: PETR4.SA).
    start, end :
        Intervalo inclusivo ISO ou date.
    provider :
        Nome do provedor (padrão yfinance). Ignorado se download_result for injetado.
    allow_partial :
        Se True, segue apenas com ativos disponíveis após falhas parciais.
    config :
        Limites e política de preços.
    download_result :
        Permite injetar fixtures em testes sem rede.
    """
    cfg = config or PipelineConfig()
    norms, d_start, d_end = validate_request(tickers, start, end, cfg)

    if download_result is not None:
        result = download_result
    elif provider == "yfinance":
        result = YFinanceProvider(cfg).download(norms, d_start, d_end)
    else:
        raise ProviderError(f"Provedor não suportado: {provider}")

    return run_from_provider_result(
        result,
        norms,
        d_start,
        d_end,
        allow_partial=allow_partial,
        config=cfg,
        analysis_id=analysis_id,
        parent_analysis_id=parent_analysis_id,
    )
