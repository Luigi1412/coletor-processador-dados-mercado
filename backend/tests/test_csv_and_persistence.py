"""Testes de CSV, persistência, exportações e consistência API/núcleo."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from market_data_pipeline.api import app
from market_data_pipeline.exceptions import ValidationError
from market_data_pipeline.exports import export_all
from market_data_pipeline.persistence import load_analysis, save_analysis
from market_data_pipeline.pipeline import run_from_provider_result
from market_data_pipeline.providers.csv_provider import (
    annualized_to_daily,
    load_external_csv,
    transform_series_to_daily_returns,
)


def test_csv_price_series(tmp_path: Path):
    p = tmp_path / "serie.csv"
    p.write_text("date,value\n2024-01-02,100\n2024-01-03,110\n2024-01-04,99\n", encoding="utf-8")
    series, meta = load_external_csv(
        p, ticker="EXT1", series_type="price", unit="BRL", frequency="daily", currency="BRL", source="fixture"
    )
    rets = transform_series_to_daily_returns(series, "price")
    assert rets.iloc[0] == pytest.approx(0.10)
    assert meta["series_type"] == "price"


def test_csv_daily_rate_not_price_variation(tmp_path: Path):
    p = tmp_path / "cdi.csv"
    p.write_text("date,value\n2024-01-02,0.0004\n2024-01-03,0.0004\n", encoding="utf-8")
    series, meta = load_external_csv(
        p,
        ticker="CDI_DAILY",
        series_type="daily_rate",
        unit="decimal",
        frequency="daily",
        currency="BRL",
        source="fixture",
    )
    rets = transform_series_to_daily_returns(series, "daily_rate")
    # Deve usar a taxa diretamente, NÃO 0.0004/0.0004 - 1 = 0
    assert rets.iloc[0] == pytest.approx(0.0004)
    assert "marcação a mercado" in meta["note"].lower() or "taxa" in meta["note"].lower()


def test_csv_annualized_conversion():
    r = annualized_to_daily(0.1215, 252)
    assert r == pytest.approx((1.1215) ** (1 / 252) - 1)


def test_csv_rejects_non_positive_price(tmp_path: Path):
    p = tmp_path / "bad.csv"
    p.write_text("date,value\n2024-01-02,0\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_external_csv(
            p, ticker="X", series_type="price", unit="BRL", frequency="daily", currency="BRL", source="t"
        )


def test_save_and_reload(known_prices_download, config):
    result = run_from_provider_result(
        known_prices_download,
        ["AAA", "BBB"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        config=config,
    )
    path = save_analysis(result, config)
    assert (path / "returns.parquet").exists()
    loaded = load_analysis(result.metadata.analysis_id, config)
    pd.testing.assert_frame_equal(loaded.returns, result.returns, check_freq=False)
    assert loaded.metadata.analysis_id == result.metadata.analysis_id
    assert loaded.metrics["AAA"].mean_daily == pytest.approx(result.metrics["AAA"].mean_daily)


def test_exports_match_analysis(known_prices_download, config, tmp_path):
    result = run_from_provider_result(
        known_prices_download,
        ["AAA", "BBB"],
        date(2024, 1, 2),
        date(2024, 1, 4),
        config=config,
    )
    paths = export_all(result, tmp_path / "out")
    rets = pd.read_csv(paths["returns_csv"], index_col=0)
    assert list(rets.columns) == ["AAA", "BBB"]
    assert abs(rets["AAA"].iloc[0] - 0.10) < 1e-12
    assert Path(paths["excel"]).exists()
    md = Path(paths["report_md"]).read_text(encoding="utf-8")
    assert "Relatório descritivo" in md
    assert result.metadata.analysis_id in md


def test_api_health_and_create_with_fixture(monkeypatch, known_prices_download, config, tmp_path):
    """Garante que a API usa o mesmo núcleo (monkeypatch do download)."""
    import market_data_pipeline.api as api_mod
    from market_data_pipeline.providers.yfinance_provider import YFinanceProvider

    monkeypatch.setattr(api_mod, "CONFIG", config)
    monkeypatch.setattr(
        YFinanceProvider,
        "download",
        lambda self, tickers, start, end: known_prices_download,
    )

    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"

    resp = client.post(
        "/analyses",
        json={"tickers": ["AAA", "BBB"], "start": "2024-01-02", "end": "2024-01-04", "allow_partial": False},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["returns"]["columns"] == ["AAA", "BBB"]
    assert body["returns"]["data"][0][0] == pytest.approx(0.10)

    aid = body["analysis_id"]
    reopen = client.get(f"/analyses/{aid}")
    assert reopen.status_code == 200
    assert reopen.json()["analysis_id"] == aid

    metrics = client.get(f"/analyses/{aid}/metrics")
    assert metrics.status_code == 200
    assert "AAA" in metrics.json()["metrics"]


def test_api_partial_conflict(monkeypatch, partial_failure_download, config):
    import market_data_pipeline.api as api_mod
    from market_data_pipeline.providers.yfinance_provider import YFinanceProvider

    monkeypatch.setattr(api_mod, "CONFIG", config)
    monkeypatch.setattr(
        YFinanceProvider,
        "download",
        lambda self, tickers, start, end: partial_failure_download,
    )
    client = TestClient(app)
    resp = client.post(
        "/analyses",
        json={"tickers": ["OK1", "BAD1"], "start": "2024-01-02", "end": "2024-01-04", "allow_partial": False},
    )
    assert resp.status_code == 409
    ok = client.post(
        "/analyses",
        json={"tickers": ["OK1", "BAD1"], "start": "2024-01-02", "end": "2024-01-04", "allow_partial": True},
    )
    assert ok.status_code == 200
