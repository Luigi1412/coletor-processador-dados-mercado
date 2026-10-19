"""Tratamento conservador de preços e cálculo de retornos válidos."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from market_data_pipeline.models import AssetQuality, GapRecord


@dataclass
class TreatedAsset:
    ticker: str
    prices: pd.Series  # preços limpos (sem dup, ordenados)
    valid_returns: pd.Series  # retornos diários válidos (sem atravessar lacuna)
    quality: AssetQuality
    gaps: list[GapRecord] = field(default_factory=list)


def _dedup_sort(prices: pd.Series) -> tuple[pd.Series, int]:
    s = prices.copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    s = s.sort_index()
    before = len(s)
    # Manter última observação do dia
    s = s[~s.index.normalize().duplicated(keep="last")]
    # Remover não finitos
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    duplicates_removed = before - len(s)
    return s.astype(float), max(0, duplicates_removed)


def classify_gaps(
    ticker: str,
    dates: pd.DatetimeIndex,
    market_calendar: pd.DatetimeIndex | None,
) -> tuple[list[GapRecord], int, int]:
    """Classifica lacunas entre datas consecutivas da série do ativo.

    Regra de consecutividade no calendário aplicável:
    - Se houver calendário de mercado (união de pregões observados no lote),
      uma ausência de N dias de calendário em que peers negociaram é lacuna inesperada.
    - Se o próximo pregão do ativo for o próximo dia do calendário de mercado
      (ainda que haja fins de semana no meio), não é lacuna inesperada.
    - Sem calendário suficiente → indeterminado quando o gap em dias corridos > 5.
    """
    gaps: list[GapRecord] = []
    unexpected = 0
    indeterminate = 0
    calendar_notes = 0

    if len(dates) < 2:
        return gaps, calendar_notes, indeterminate

    cal_set = set(pd.DatetimeIndex(market_calendar).normalize()) if market_calendar is not None else None
    norm_dates = dates.normalize()

    for i in range(1, len(norm_dates)):
        prev = norm_dates[i - 1]
        curr = norm_dates[i]
        # Dias de mercado estritamente entre prev e curr
        if cal_set is not None and len(cal_set) >= 2:
            between = [d for d in sorted(cal_set) if prev < d < curr]
            if between:
                for d in between:
                    gaps.append(
                        GapRecord(
                            ticker=ticker,
                            date=pd.Timestamp(d).date().isoformat(),
                            kind="unexpected",
                            detail="Peers do lote negociaram e o ativo não possui cotação neste dia.",
                        )
                    )
                unexpected += len(between)
            else:
                # Pode haver sábado/domingo — calendário sem negociação
                calendar_days = (curr - prev).days
                if calendar_days > 1:
                    calendar_notes += 1
        else:
            calendar_days = (curr - prev).days
            if calendar_days > 5:
                gaps.append(
                    GapRecord(
                        ticker=ticker,
                        date=prev.date().isoformat(),
                        kind="indeterminate",
                        detail=(
                            f"Gap de {calendar_days} dias corridos sem calendário de mercado "
                            "suficiente para classificar a causa."
                        ),
                    )
                )
                indeterminate += 1
            elif calendar_days > 1:
                calendar_notes += 1

    return gaps, calendar_notes, indeterminate


def compute_valid_daily_returns(
    prices: pd.Series,
    ticker: str,
    market_calendar: pd.DatetimeIndex | None = None,
) -> TreatedAsset:
    """Calcula retornos simples apenas entre observações consecutivas no calendário aplicável.

    r_t = P_t / P_(t-1) - 1

    Não calcula retorno atravessando lacuna inesperada: se há pregões de mercado
    entre duas cotações do ativo, o par (P_prev, P_curr) é descartado para o
    retorno 'diário'.
    """
    clean, dup_removed = _dedup_sort(prices)
    gaps, calendar_notes, indeterminate = classify_gaps(ticker, clean.index, market_calendar)

    unexpected_dates = {g.date for g in gaps if g.kind == "unexpected"}

    returns_idx: list[pd.Timestamp] = []
    returns_val: list[float] = []

    cal_set = set(pd.DatetimeIndex(market_calendar).normalize()) if market_calendar is not None else None
    norm = clean.index.normalize()

    for i in range(1, len(clean)):
        prev_ts = norm[i - 1]
        curr_ts = norm[i]
        # Verificar se há lacuna inesperada entre prev e curr
        if cal_set is not None:
            between = [d for d in cal_set if prev_ts < d < curr_ts]
            if between:
                # Não atravessar lacuna — não gera retorno diário para este par
                continue
        else:
            # Sem calendário: se gap indeterminado (>5 dias), não atravessar
            if (curr_ts - prev_ts).days > 5:
                continue

        p0 = float(clean.iloc[i - 1])
        p1 = float(clean.iloc[i])
        if p0 == 0 or not np.isfinite(p0) or not np.isfinite(p1):
            continue
        r = p1 / p0 - 1.0
        if not np.isfinite(r):
            continue
        returns_idx.append(clean.index[i])
        returns_val.append(r)

    valid_returns = pd.Series(returns_val, index=pd.DatetimeIndex(returns_idx), name=ticker)

    quality = AssetQuality(
        ticker=ticker,
        observations_raw=len(prices),
        observations_after_dedup=len(clean),
        observations_with_valid_returns=len(valid_returns),
        observations_aligned=0,  # preenchido no alinhamento
        duplicates_removed=dup_removed,
        unexpected_gaps=sorted(unexpected_dates),
        calendar_absences_noted=calendar_notes,
        indeterminate_gaps=indeterminate,
        available=True,
    )
    return TreatedAsset(
        ticker=ticker,
        prices=clean,
        valid_returns=valid_returns,
        quality=quality,
        gaps=gaps,
    )


def build_market_calendar(price_map: dict[str, pd.Series]) -> pd.DatetimeIndex:
    """Calendário aproximado: união das datas com cotação no lote."""
    if not price_map:
        return pd.DatetimeIndex([])
    all_dates: list[pd.Timestamp] = []
    for s in price_map.values():
        all_dates.extend(list(pd.DatetimeIndex(s.index).normalize()))
    return pd.DatetimeIndex(sorted(set(all_dates)))


def align_returns(
    treated: list[TreatedAsset],
    min_observations: int = 2,
) -> tuple[pd.DataFrame, list[str], float | None]:
    """Alinha retornos válidos pela interseção de datas.

    Retorna DataFrame sem NaN/inf, lista de datas removidas (união - interseção
    relativa a cada ativo agregada), e ratio de cobertura.
    """
    if not treated:
        return pd.DataFrame(), [], None

    series_list = [t.valid_returns for t in treated if len(t.valid_returns) > 0]
    if not series_list:
        return pd.DataFrame(), [], None

    # União e interseção
    index_sets = [set(s.index.normalize()) for s in series_list]
    intersection = set.intersection(*index_sets) if index_sets else set()
    union = set.union(*index_sets) if index_sets else set()

    if not intersection:
        return pd.DataFrame(), sorted(d.date().isoformat() for d in union), 0.0

    common = pd.DatetimeIndex(sorted(intersection))
    aligned = pd.DataFrame({t.ticker: t.valid_returns.groupby(t.valid_returns.index.normalize()).last() for t in treated})
    aligned = aligned.reindex(common).sort_index()

    # Remover qualquer residual não finito
    aligned = aligned.replace([np.inf, -np.inf], np.nan)
    if aligned.isna().any().any():
        # Dropar linhas com qualquer NaN (não deveria ocorrer na interseção limpa)
        aligned = aligned.dropna(how="any")

    if len(aligned) < min_observations:
        removed = sorted(d.date().isoformat() for d in (union - set(aligned.index.normalize())))
        return pd.DataFrame(), removed, None

    removed_dates = sorted(d.date().isoformat() for d in (union - set(aligned.index.normalize())))
    coverage = len(aligned) / len(union) if union else None

    for t in treated:
        t.quality.observations_aligned = int(len(aligned))

    return aligned.astype(float), removed_dates, coverage
