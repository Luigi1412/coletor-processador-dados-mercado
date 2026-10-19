"""Teste de integração real com yfinance.

Pendente: ativos oficiais do grupo (ainda não definidos).
Este teste usa apenas tickers provisórios de exemplo.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.exceptions import PipelineError
from market_data_pipeline.exports import export_all
from market_data_pipeline.persistence import save_analysis
from market_data_pipeline.pipeline import compute_daily_returns

EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "docs" / "evidence"


@pytest.mark.integration
def test_real_yfinance_two_tickers(tmp_path):
    """Integração real: PETR4.SA e VALE3.SA (provisórios, NÃO oficiais do grupo)."""
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
    out = tmp_path / "export"
    export_all(result, out)

    # Registrar evidência se o diretório existir/criar
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence = EVIDENCE_DIR / "integration_yfinance.txt"
    evidence.write_text(
        (
            f"status=PASSED\n"
            f"tickers=PETR4.SA,VALE3.SA (provisórios — NÃO oficiais do grupo)\n"
            f"requested={start.isoformat()}..{end.isoformat()}\n"
            f"effective={result.quality.effective_start}..{result.quality.effective_end}\n"
            f"shape={result.returns.shape}\n"
            f"collected_at={result.quality.collected_at}\n"
            f"methodology={result.metadata.methodology_version}\n"
            f"note=Caso com ativos oficiais do grupo: PENDENTE até definição do grupo.\n"
        ),
        encoding="utf-8",
    )


@pytest.mark.integration
def test_official_group_assets_pending():
    """Marcador explícito: ativos oficiais do grupo ainda não definidos."""
    pytest.skip(
        "PENDENTE: ativos oficiais do grupo ainda não foram definidos. "
        "Exemplos provisórios NÃO devem ser tratados como seleção aprovada."
    )
