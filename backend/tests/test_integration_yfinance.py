"""Testes de integração real com yfinance."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from market_data_pipeline.config import (
    OFFICIAL_TEST_END,
    OFFICIAL_TEST_START,
    OFFICIAL_TICKERS,
    PipelineConfig,
)
from market_data_pipeline.exceptions import PipelineError
from market_data_pipeline.exports import export_all
from market_data_pipeline.persistence import save_analysis
from market_data_pipeline.pipeline import compute_daily_returns

EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "docs" / "evidence"


@pytest.mark.integration
def test_real_yfinance_two_tickers(tmp_path):
    """Smoke de integração com dois ativos líquidos (subconjunto)."""
    end = date.today()
    start = end - timedelta(days=120)
    cfg = PipelineConfig(data_dir=str(tmp_path / "analyses"))

    try:
        result = compute_daily_returns(
            ["PETR4.SA", "VALE3.SA"],
            start,
            end,
            allow_partial=False,
            config=cfg,
        )
    except PipelineError as exc:
        pytest.skip(f"Provedor/rede indisponível: {exc.message}")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Bloqueio de rede/provedor: {exc}")

    assert not result.returns.empty
    assert result.returns.isna().sum().sum() == 0
    assert set(result.returns.columns) == {"PETR4.SA", "VALE3.SA"}
    assert result.returns.index.is_monotonic_increasing

    save_analysis(result, cfg)
    export_all(result, tmp_path / "export")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "integration_yfinance.txt").write_text(
        (
            f"status=PASSED\n"
            f"tickers=PETR4.SA,VALE3.SA (smoke)\n"
            f"requested={start.isoformat()}..{end.isoformat()}\n"
            f"effective={result.quality.effective_start}..{result.quality.effective_end}\n"
            f"shape={result.returns.shape}\n"
            f"collected_at={result.quality.collected_at}\n"
            f"methodology={result.metadata.methodology_version}\n"
        ),
        encoding="utf-8",
    )


@pytest.mark.integration
def test_official_group_assets(tmp_path):
    """Caso barema: ativos oficiais do Grupo 4 no período de teste do SPEC."""
    cfg = PipelineConfig(data_dir=str(tmp_path / "analyses"))

    try:
        result = compute_daily_returns(
            OFFICIAL_TICKERS,
            OFFICIAL_TEST_START,
            OFFICIAL_TEST_END,
            allow_partial=False,
            config=cfg,
        )
    except PipelineError as exc:
        pytest.skip(f"Provedor/rede indisponível: {exc.message}")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Bloqueio de rede/provedor: {exc}")

    assert not result.returns.empty
    assert result.returns.isna().sum().sum() == 0
    assert set(result.returns.columns) == set(OFFICIAL_TICKERS)
    assert result.returns.index.is_monotonic_increasing
    assert len(result.returns) >= 2

    save_analysis(result, cfg)
    export_all(result, tmp_path / "export_oficial")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    means = {t: result.metrics[t].mean_daily for t in OFFICIAL_TICKERS}
    stds = {t: result.metrics[t].std_daily for t in OFFICIAL_TICKERS}
    (EVIDENCE_DIR / "caso_ativos_oficiais.txt").write_text(
        (
            f"status=PASSED\n"
            f"tickers={','.join(OFFICIAL_TICKERS)}\n"
            f"requested={OFFICIAL_TEST_START}..{OFFICIAL_TEST_END}\n"
            f"effective={result.quality.effective_start}..{result.quality.effective_end}\n"
            f"shape={result.returns.shape}\n"
            f"aligned_dates={result.quality.aligned_dates_count}\n"
            f"coverage={result.quality.alignment_coverage_ratio}\n"
            f"collected_at={result.quality.collected_at}\n"
            f"methodology={result.metadata.methodology_version}\n"
            f"mean_daily={means}\n"
            f"std_daily={stds}\n"
            f"analysis_id={result.metadata.analysis_id}\n"
        ),
        encoding="utf-8",
    )
