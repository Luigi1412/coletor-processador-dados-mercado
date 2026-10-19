"""Coletor e Processador de Dados de Mercado — núcleo compartilhado."""

from market_data_pipeline.pipeline import compute_daily_returns, PipelineResult
from market_data_pipeline.config import PipelineConfig, METHODOLOGY_VERSION

__all__ = [
    "compute_daily_returns",
    "PipelineResult",
    "PipelineConfig",
    "METHODOLOGY_VERSION",
]

__version__ = "1.0.0"
