"""Fixtures de teste — dados sintéticos identificados, sem rede."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.providers.base import ProviderDownloadResult


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(data_dir=str(tmp_path / "analyses"))


def _series(dates: list[str], values: list[float], name: str) -> pd.Series:
    idx = pd.to_datetime(dates)
    return pd.Series(values, index=idx, name=name, dtype=float)


@pytest.fixture
def known_prices_download() -> ProviderDownloadResult:
    """Preços conhecidos para retornos manuais.

    A: 100, 110, 99 → r = 0.10, -0.10
    B: 50, 55, 52.25 → r = 0.10, -0.05
    Datas consecutivas de pregão (sem lacuna).
    """
    dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
    return ProviderDownloadResult(
        prices={
            "AAA": _series(dates, [100.0, 110.0, 99.0], "AAA"),
            "BBB": _series(dates, [50.0, 55.0, 52.25], "BBB"),
        },
        failed={},
        currencies={"AAA": "BRL", "BBB": "BRL"},
        source="test_fixture",
        collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        raw_notes=["Fixture de teste — dados sintéticos."],
    )


@pytest.fixture
def gap_prices_download() -> ProviderDownloadResult:
    """Lacuna intermediária: A falta em 2024-01-03 enquanto B negocia.

    Após o buraco, há dias suficientes para interseção >= 2 observações.
    """
    return ProviderDownloadResult(
        prices={
            "GAPA": _series(
                ["2024-01-02", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"],
                [100.0, 121.0, 110.0, 115.0, 120.0],
                "GAPA",
            ),
            "GAPB": _series(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                    "2024-01-09",
                ],
                [10.0, 11.0, 12.0, 11.0, 10.5, 10.0],
                "GAPB",
            ),
        },
        failed={},
        currencies={"GAPA": "BRL", "GAPB": "BRL"},
        source="test_fixture",
        collected_at="2024-01-09T12:00:00Z",
        raw_notes=["Fixture lacuna intermediária."],
    )


@pytest.fixture
def duplicate_unsorted_download() -> ProviderDownloadResult:
    idx = pd.to_datetime(["2024-01-04", "2024-01-02", "2024-01-02", "2024-01-03"])
    s = pd.Series([103.0, 100.0, 101.0, 102.0], index=idx, name="DUP")
    return ProviderDownloadResult(
        prices={"DUP": s, "OK": _series(["2024-01-02", "2024-01-03", "2024-01-04"], [1, 1.1, 1.2], "OK")},
        failed={},
        currencies={"DUP": "BRL", "OK": "BRL"},
        source="test_fixture",
        collected_at="2024-01-05T12:00:00Z",
        raw_notes=["Fixture duplicatas/desordem."],
    )


@pytest.fixture
def constant_series_download() -> ProviderDownloadResult:
    dates = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    return ProviderDownloadResult(
        prices={
            "CONST": _series(dates, [100.0, 100.0, 100.0, 100.0], "CONST"),
            "VAR": _series(dates, [100.0, 110.0, 105.0, 115.0], "VAR"),
        },
        failed={},
        currencies={"CONST": "BRL", "VAR": "BRL"},
        source="test_fixture",
        collected_at="2024-01-05T12:00:00Z",
        raw_notes=["Fixture série constante."],
    )


@pytest.fixture
def partial_failure_download() -> ProviderDownloadResult:
    dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
    return ProviderDownloadResult(
        prices={"OK1": _series(dates, [100, 101, 102], "OK1")},
        failed={"BAD1": "Resposta vazia ou ticker sem dados no intervalo."},
        currencies={"OK1": "BRL"},
        source="test_fixture",
        collected_at="2024-01-05T12:00:00Z",
        raw_notes=["Fixture falha parcial."],
    )


@pytest.fixture
def empty_download() -> ProviderDownloadResult:
    return ProviderDownloadResult(
        prices={},
        failed={"X": "vazio"},
        currencies={},
        source="test_fixture",
        collected_at="2024-01-05T12:00:00Z",
        raw_notes=["Fixture vazia."],
    )


@pytest.fixture
def no_intersection_download() -> ProviderDownloadResult:
    return ProviderDownloadResult(
        prices={
            "A1": _series(["2024-01-02", "2024-01-03"], [100, 110], "A1"),
            "B1": _series(["2024-02-02", "2024-02-03"], [50, 55], "B1"),
        },
        failed={},
        currencies={"A1": "BRL", "B1": "BRL"},
        source="test_fixture",
        collected_at="2024-01-05T12:00:00Z",
        raw_notes=["Fixture sem interseção."],
    )
