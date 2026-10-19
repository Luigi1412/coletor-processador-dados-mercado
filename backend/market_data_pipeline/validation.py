"""Validação de entradas do pipeline."""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.exceptions import ValidationError


def parse_date(value: str | date) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(
            f"Data inválida '{value}'. Use o formato ISO YYYY-MM-DD.",
            details={"value": value},
        ) from exc


def normalize_tickers(tickers: Sequence[str]) -> list[str]:
    if tickers is None:
        raise ValidationError("A lista de tickers é obrigatória.")
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in tickers:
        if raw is None:
            continue
        t = str(raw).strip().upper()
        if not t:
            raise ValidationError("Ticker vazio não é permitido.")
        if t in seen:
            continue
        seen.add(t)
        cleaned.append(t)
    if not cleaned:
        raise ValidationError("Informe ao menos um ticker.")
    return cleaned


def validate_request(
    tickers: Sequence[str],
    start: str | date,
    end: str | date,
    config: PipelineConfig | None = None,
) -> tuple[list[str], date, date]:
    """Valida tickers e intervalo; retorna valores normalizados."""
    cfg = config or PipelineConfig()
    norms = normalize_tickers(tickers)
    if len(norms) > cfg.max_tickers:
        raise ValidationError(
            f"No máximo {cfg.max_tickers} ativos por análise (recebidos: {len(norms)}).",
            details={"max_tickers": cfg.max_tickers, "received": len(norms)},
        )

    d_start = parse_date(start)
    d_end = parse_date(end)
    if d_start >= d_end:
        raise ValidationError(
            "A data inicial deve ser estritamente anterior à data final.",
            details={"start": d_start.isoformat(), "end": d_end.isoformat()},
        )

    span_years = (d_end - d_start).days / 365.25
    if span_years > cfg.max_history_years:
        raise ValidationError(
            f"Intervalo acima do limite de segurança ({cfg.max_history_years} anos).",
            details={"span_years": span_years},
        )

    return norms, d_start, d_end
