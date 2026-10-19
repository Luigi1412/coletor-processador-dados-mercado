"""Cálculos de métricas financeiras descritivas."""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_data_pipeline.models import AssetMetrics


def wealth_path(returns: pd.Series, base: float = 1.0) -> pd.Series:
    """Trajetória de riqueza por composição: W_t = W_{t-1} * (1 + r_t)."""
    r = returns.astype(float)
    w = (1.0 + r).cumprod() * base
    return w


def drawdown_series(returns: pd.Series, base: float = 1.0) -> pd.Series:
    """Drawdown a partir da trajetória de riqueza com base explícita."""
    w = wealth_path(returns, base=base)
    peak = w.cummax()
    dd = w / peak - 1.0
    return dd


def max_drawdown(returns: pd.Series, base: float = 1.0) -> float | None:
    if returns is None or len(returns) == 0:
        return None
    dd = drawdown_series(returns, base=base)
    val = float(dd.min())
    return val if np.isfinite(val) else None


def cumulative_return(returns: pd.Series) -> float | None:
    """Retorno acumulado por composição: prod(1+r) - 1."""
    if returns is None or len(returns) == 0:
        return None
    r = returns.astype(float)
    val = float(np.prod(1.0 + r.to_numpy()) - 1.0)
    return val if np.isfinite(val) else None


def compute_asset_metrics(ticker: str, returns: pd.Series, wealth_base: float = 1.0) -> AssetMetrics:
    r = returns.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    n = len(r)
    if n == 0:
        return AssetMetrics(
            ticker=ticker,
            n_observations=0,
            mean_daily=None,
            std_daily=None,
            min_daily=None,
            max_daily=None,
            cumulative_return=None,
            max_drawdown=None,
        )
    mean = float(r.mean())
    std = float(r.std(ddof=1)) if n >= 2 else None
    return AssetMetrics(
        ticker=ticker,
        n_observations=n,
        mean_daily=mean,
        std_daily=std if std is not None and np.isfinite(std) else None,
        min_daily=float(r.min()),
        max_daily=float(r.max()),
        cumulative_return=cumulative_return(r),
        max_drawdown=max_drawdown(r, base=wealth_base),
        mean_is_historical_estimate=True,
    )


def compute_all_metrics(returns: pd.DataFrame, wealth_base: float = 1.0) -> dict[str, AssetMetrics]:
    return {col: compute_asset_metrics(col, returns[col], wealth_base=wealth_base) for col in returns.columns}


def compute_correlation(returns: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlação de Pearson.

    Séries constantes ou pares com amostra insuficiente → NaN (não definido),
    nunca correl = 0 inventado.
    """
    cols = list(returns.columns)
    n = len(cols)
    mat = pd.DataFrame(np.nan, index=cols, columns=cols, dtype=float)
    if n == 0 or len(returns) < 2:
        return mat

    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i == j:
                sa = returns[a]
                if sa.nunique(dropna=True) <= 1:
                    mat.loc[a, b] = np.nan  # constante: auto-correlação não definida
                else:
                    mat.loc[a, b] = 1.0
                continue
            pair = returns[[a, b]].dropna()
            if len(pair) < 2:
                mat.loc[a, b] = np.nan
                continue
            if pair[a].nunique() <= 1 or pair[b].nunique() <= 1:
                mat.loc[a, b] = np.nan
                continue
            corr = pair[a].corr(pair[b])
            mat.loc[a, b] = float(corr) if corr is not None and np.isfinite(corr) else np.nan
    return mat


def correlation_undefined_reason(returns: pd.DataFrame, a: str, b: str) -> str | None:
    """Explica por que a correlação é não definida, se aplicável."""
    if a not in returns.columns or b not in returns.columns:
        return "Ativo ausente na amostra alinhada."
    pair = returns[[a, b]].dropna()
    if len(pair) < 2:
        return "Amostra insuficiente (< 2 observações comuns)."
    if pair[a].nunique() <= 1 or pair[b].nunique() <= 1:
        return "Série constante (variância zero) — correlação não definida."
    return None
