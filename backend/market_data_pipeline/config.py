"""Configuração do pipeline e defaults provisórios."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

METHODOLOGY_VERSION = "1.0.0"

# Lista provisória — NÃO é a seleção oficial do grupo.
PROVISIONAL_TICKERS: list[str] = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "WEGE3.SA",
]

PriceField = Literal["Adj Close", "Close"]


@dataclass
class PipelineConfig:
    """Parâmetros operacionais e de política do pipeline.

    Decisões principais:
    - price_field="Adj Close": preços já ajustados por dividendos/splits no Yahoo;
      evita aplicar um segundo fator de ajuste (ajuste duplicado).
    - max_tickers=30: limite razoável para análise exploratória local.
    - download_timeout_s / max_retries: resiliência a falhas transitórias do provedor.
    """

    price_field: PriceField = "Adj Close"
    max_tickers: int = 30
    download_timeout_s: float = 60.0
    max_retries: int = 3
    retry_backoff_s: float = 1.5
    max_history_years: int = 40
    wealth_base: float = 1.0
    business_days_per_year: int = 252
    min_observations: int = 2
    data_dir: str = "data/analyses"
    provider_name: str = "yfinance"


def default_start_end(years: int = 2) -> tuple[date, date]:
    """Período inicial sugerido na interface (~2 anos)."""
    end = date.today()
    start = end - timedelta(days=365 * years)
    return start, end
