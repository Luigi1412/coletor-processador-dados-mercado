"""Importação validada de séries externas via CSV."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.exceptions import ValidationError
from market_data_pipeline.models import SeriesType
from market_data_pipeline.providers.base import ProviderDownloadResult


REQUIRED_COLUMNS = {"date", "value"}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def annualized_to_daily(rate: float, business_days: int = 252) -> float:
    """Converte taxa anualizada para taxa diária equivalente (dias úteis).

    (1 + r_annual)^(1/252) - 1
    """
    return (1.0 + rate) ** (1.0 / business_days) - 1.0


def transform_series_to_daily_returns(
    values: pd.Series,
    series_type: SeriesType,
    business_days: int = 252,
) -> pd.Series:
    """Transforma série externa em retornos diários conforme o tipo declarado."""
    s = values.astype(float).sort_index()
    if series_type in ("price", "return_index"):
        # Variação percentual do nível — NÃO usar para taxas CDI
        prev = s.shift(1)
        ret = s / prev - 1.0
        return ret.dropna()
    if series_type == "daily_rate":
        return s.dropna()
    if series_type == "annualized_rate":
        return s.dropna().map(lambda r: annualized_to_daily(r, business_days))
    raise ValidationError(f"Tipo de série não suportado: {series_type}")


def load_external_csv(
    path_or_file: str | Path | BinaryIO,
    *,
    ticker: str,
    series_type: SeriesType,
    unit: str,
    frequency: str,
    currency: str,
    source: str,
    config: PipelineConfig | None = None,
) -> tuple[pd.Series, dict]:
    """Carrega e valida CSV externo; retorna série de valores brutos + metadados."""
    cfg = config or PipelineConfig()
    df = pd.read_csv(path_or_file)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValidationError(
            f"CSV inválido: colunas obrigatórias ausentes: {sorted(missing)}. "
            "Esperado: date,value (opcional: unit,frequency,currency,source,series_type).",
            details={"missing": sorted(missing)},
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValidationError("CSV contém datas inválidas na coluna 'date'.")

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if df["value"].isna().any():
        raise ValidationError("CSV contém valores não numéricos na coluna 'value'.")

    # Validação de coerência de tipo
    if series_type in ("daily_rate", "annualized_rate"):
        if unit.lower() not in {"decimal", "rate", "taxa", "percent", "%"}:
            raise ValidationError(
                f"Para series_type={series_type}, informe unit adequada "
                f"(ex.: 'decimal'). Recebido: '{unit}'. "
                "Não trate CDI como preço de ativo.",
            )
        if (df["value"] < -1).any() and series_type == "daily_rate":
            raise ValidationError("Taxa diária em decimal fora de faixa plausível (< -100%).")

    if series_type in ("price", "return_index") and (df["value"] <= 0).any():
        raise ValidationError("Preços/índices devem ser estritamente positivos.")

    series = pd.Series(df["value"].values, index=pd.DatetimeIndex(df["date"]), name=ticker)
    series = series.sort_index()
    # Dedup: última observação do dia
    series = series[~series.index.duplicated(keep="last")]

    meta = {
        "ticker": ticker,
        "series_type": series_type,
        "unit": unit,
        "frequency": frequency,
        "currency": currency,
        "source": source,
        "transformations": [],
        "business_days_per_year": cfg.business_days_per_year,
        "note": (
            "Série de taxa não deve ser interpretada como preço de ativo "
            "nem como instrumento de RF com marcação a mercado."
            if series_type in ("daily_rate", "annualized_rate")
            else "Série de preço/índice."
        ),
    }
    return series, meta


class CsvPriceProvider:
    """Adapta séries CSV do tipo price/return_index ao contrato de preços."""

    name = "csv"

    def __init__(self, series_map: dict[str, pd.Series], meta_map: dict[str, dict] | None = None):
        self.series_map = series_map
        self.meta_map = meta_map or {}

    def as_download_result(self) -> ProviderDownloadResult:
        return ProviderDownloadResult(
            prices=dict(self.series_map),
            failed={},
            currencies={k: self.meta_map.get(k, {}).get("currency", "UNKNOWN") for k in self.series_map},
            source="csv",
            collected_at=_utcnow_iso(),
            raw_notes=["Dados importados via CSV validado."],
        )
