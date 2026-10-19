"""Interface de provedores de preços."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import pandas as pd


@dataclass
class ProviderDownloadResult:
    """Resultado bruto de um provedor, antes do tratamento financeiro."""

    prices: dict[str, pd.Series]  # ticker -> série de preços ajustados
    failed: dict[str, str] = field(default_factory=dict)
    currencies: dict[str, str] = field(default_factory=dict)
    source: str = "unknown"
    collected_at: str = ""
    raw_notes: list[str] = field(default_factory=list)


class PriceProvider(ABC):
    name: str = "base"

    @abstractmethod
    def download(
        self,
        tickers: list[str],
        start: date,
        end: date,
    ) -> ProviderDownloadResult:
        """Baixa preços ajustados por ticker no intervalo [start, end]."""
