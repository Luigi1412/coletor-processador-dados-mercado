"""Modelos de dados do núcleo (dataclasses / tipagem)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Literal


SeriesType = Literal["price", "return_index", "daily_rate", "annualized_rate"]


@dataclass
class GapRecord:
    ticker: str
    date: str
    kind: Literal["unexpected", "calendar", "indeterminate"]
    detail: str = ""


@dataclass
class AssetQuality:
    ticker: str
    observations_raw: int
    observations_after_dedup: int
    observations_with_valid_returns: int
    observations_aligned: int
    duplicates_removed: int
    unexpected_gaps: list[str] = field(default_factory=list)
    calendar_absences_noted: int = 0
    indeterminate_gaps: int = 0
    available: bool = True
    failure_reason: str | None = None
    currency: str | None = None


@dataclass
class QualityReport:
    requested_start: str
    requested_end: str
    effective_start: str | None
    effective_end: str | None
    requested_tickers: list[str]
    available_tickers: list[str]
    unavailable_tickers: list[str]
    aligned_dates_count: int
    dates_removed_by_alignment: list[str]
    alignment_coverage_ratio: float | None
    gaps: list[GapRecord]
    assets: list[AssetQuality]
    source: str
    collected_at: str
    methodology_version: str
    notes: list[str] = field(default_factory=list)
    currencies: list[str] = field(default_factory=list)
    mixed_currencies: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssetMetrics:
    ticker: str
    n_observations: int
    mean_daily: float | None
    std_daily: float | None
    min_daily: float | None
    max_daily: float | None
    cumulative_return: float | None
    max_drawdown: float | None
    mean_is_historical_estimate: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisMetadata:
    analysis_id: str
    tickers: list[str]
    start: str
    end: str
    allow_partial: bool
    provider: str
    source: str
    collected_at: str
    methodology_version: str
    parent_analysis_id: str | None = None
    price_field: str = "Adj Close"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
