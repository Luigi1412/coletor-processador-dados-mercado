"""Testes de correção financeira com fixtures (sem rede)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from datetime import date

from market_data_pipeline.exceptions import InsufficientDataError, PartialFailureError, ValidationError
from market_data_pipeline.metrics import (
    compute_asset_metrics,
    cumulative_return,
    drawdown_series,
    max_drawdown,
)
from market_data_pipeline.pipeline import compute_daily_returns, run_from_provider_result
from market_data_pipeline.providers.base import ProviderDownloadResult
from market_data_pipeline.providers.yfinance_provider import normalize_yfinance_frame
from market_data_pipeline.treatment import compute_valid_daily_returns, build_market_calendar


def test_known_returns(known_prices_download, config):
    result = run_from_provider_result(
        known_prices_download,
        ["AAA", "BBB"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        allow_partial=False,
        config=config,
    )
    # AAA: 100→110→99 → 0.10, -0.10
    np.testing.assert_allclose(result.returns["AAA"].tolist(), [0.10, -0.10], rtol=1e-12)
    # BBB: 50→55→52.25 → 0.10, -0.05
    np.testing.assert_allclose(result.returns["BBB"].tolist(), [0.10, -0.05], rtol=1e-12)
    assert result.returns.isna().sum().sum() == 0
    assert result.returns.index.is_unique
    assert result.returns.index.is_monotonic_increasing


def test_mean_std_min_max(known_prices_download, config):
    result = run_from_provider_result(
        known_prices_download,
        ["AAA", "BBB"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        config=config,
    )
    m = result.metrics["AAA"]
    # mean (0.1 + -0.1)/2 = 0
    assert m.mean_daily == pytest.approx(0.0)
    # std ddof=1: sqrt(((0.1)^2 + (-0.1)^2)/1) = sqrt(0.02)
    assert m.std_daily == pytest.approx(np.sqrt(0.02))
    assert m.min_daily == pytest.approx(-0.10)
    assert m.max_daily == pytest.approx(0.10)
    assert m.n_observations == 2


def test_cumulative_and_drawdown():
    # r = 0.10, -0.05 → W = 1.10, 1.045; peak 1.10; DD = 0, 1.045/1.10-1
    r = pd.Series([0.10, -0.05], index=pd.to_datetime(["2024-01-03", "2024-01-04"]))
    assert cumulative_return(r) == pytest.approx(1.10 * 0.95 - 1.0)
    dd = drawdown_series(r, base=1.0)
    assert dd.iloc[0] == pytest.approx(0.0)
    assert dd.iloc[1] == pytest.approx(1.045 / 1.10 - 1.0)
    assert max_drawdown(r) == pytest.approx(1.045 / 1.10 - 1.0)

    m = compute_asset_metrics("X", r)
    assert m.cumulative_return == pytest.approx(cumulative_return(r))
    assert m.max_drawdown == pytest.approx(max_drawdown(r))


def test_gap_does_not_create_multiday_as_daily(gap_prices_download, config):
    """GAPA: 100→121 atravessa 01-03 (peer negociou) — não deve gerar r=0.21 como diário."""
    cal = build_market_calendar(gap_prices_download.prices)
    treated = compute_valid_daily_returns(gap_prices_download.prices["GAPA"], "GAPA", cal)
    # Entre 02 e 04 há pregão 03 → par descartado; 21% multi-dia não entra
    assert all(abs(r - (121 / 100 - 1)) > 1e-12 for r in treated.valid_returns.values)
    # Primeiro retorno válido: 04→05 = 110/121 - 1
    assert treated.valid_returns.iloc[0] == pytest.approx(110 / 121 - 1)
    assert any(g.kind == "unexpected" for g in treated.gaps)

    # Pipeline alinhado: só datas com retorno válido em ambos
    result = run_from_provider_result(
        gap_prices_download,
        ["GAPA", "GAPB"],
        date(2024, 1, 2),
        date(2024, 1, 9),
        allow_partial=True,
        config=config,
    )
    # GAPA não gera retorno em 04 (atravessaria 03); interseção exclui 03
    assert "2024-01-03" not in list(result.returns.index.strftime("%Y-%m-%d"))
    assert (result.returns["GAPA"] - (121 / 100 - 1)).abs().min() > 1e-9  # 21% não aparece como diário
    assert not result.returns.isna().any().any()
    assert len(result.returns) >= 2



def test_duplicates_and_unsorted(duplicate_unsorted_download, config):
    result = run_from_provider_result(
        duplicate_unsorted_download,
        ["DUP", "OK"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        config=config,
    )
    # DUP após dedup keep last em 01-02: 101, depois 102, 103
    assert result.returns.index.is_monotonic_increasing
    assert result.quality.assets[0].duplicates_removed >= 0


def test_invalid_interval(config):
    with pytest.raises(ValidationError):
        compute_daily_returns(
            ["AAA"],
            "2024-05-01",
            "2024-01-01",
            download_result=ProviderDownloadResult(prices={}, failed={}, source="t", collected_at="x"),
            config=config,
        )


def test_empty_response(empty_download, config):
    with pytest.raises(InsufficientDataError):
        run_from_provider_result(
            empty_download,
            ["X"],
            date(2024, 1, 2),
            date(2024, 1, 4),
            config=config,
        )


def test_partial_failure_requires_flag(partial_failure_download, config):
    with pytest.raises(PartialFailureError) as ei:
        run_from_provider_result(
            partial_failure_download,
            ["OK1", "BAD1"],
            date(2024, 1, 2),
            date(2024, 1, 4),
            allow_partial=False,
            config=config,
        )
    assert "BAD1" in ei.value.failed
    assert "OK1" in ei.value.available

    result = run_from_provider_result(
        partial_failure_download,
        ["OK1", "BAD1"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        allow_partial=True,
        config=config,
    )
    assert list(result.returns.columns) == ["OK1"]


def test_no_intersection(no_intersection_download, config):
    with pytest.raises(InsufficientDataError):
        run_from_provider_result(
            no_intersection_download,
            ["A1", "B1"],
            date(2024, 1, 1),
            date(2024, 3, 1),
            config=config,
        )


def test_constant_correlation_undefined(constant_series_download, config):
    result = run_from_provider_result(
        constant_series_download,
        ["CONST", "VAR"],
        date(2024, 1, 2),
        date(2024, 1, 5),
        config=config,
    )
    # CONST retornos todos 0 → constante → corr não definida
    assert np.isnan(result.correlation.loc["CONST", "VAR"])
    assert np.isnan(result.correlation.loc["CONST", "CONST"])


def test_insufficient_sample(config):
    dl = ProviderDownloadResult(
        prices={"S": pd.Series([100.0], index=pd.to_datetime(["2024-01-02"]))},
        failed={},
        currencies={"S": "BRL"},
        source="t",
        collected_at="x",
    )
    with pytest.raises((InsufficientDataError, PartialFailureError)):
        run_from_provider_result(dl, ["S"], date(2024, 1, 2), date(2024, 1, 3), allow_partial=True, config=config)


def test_normalize_yfinance_multiindex():
    arrays = [
        ["Adj Close", "Adj Close", "Close", "Close"],
        ["T1", "T2", "T1", "T2"],
    ]
    cols = pd.MultiIndex.from_arrays(arrays)
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    df = pd.DataFrame([[10.0, 20.0, 11.0, 21.0], [11.0, 22.0, 12.0, 23.0]], index=idx, columns=cols)
    parsed = normalize_yfinance_frame(df, ["T1", "T2"], "Adj Close")
    assert "T1" in parsed and "T2" in parsed
    assert parsed["T1"].iloc[0] == 10.0


def test_ticker_validation(config):
    with pytest.raises(ValidationError):
        compute_daily_returns([], "2024-01-01", "2024-06-01", config=config)
    with pytest.raises(ValidationError):
        compute_daily_returns([""], "2024-01-01", "2024-06-01", config=config)
