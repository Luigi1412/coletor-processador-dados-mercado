"""Serialização para API JSON."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from market_data_pipeline.pipeline import PipelineResult


def df_to_records(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {"index": [], "columns": [], "data": []}
    idx = [str(i.date()) if hasattr(i, "date") else str(i) for i in df.index]
    cols = [str(c) for c in df.columns]
    data = []
    for row in df.itertuples(index=False, name=None):
        data.append([None if (v is None or (isinstance(v, float) and not np.isfinite(v))) else float(v) for v in row])
    return {"index": idx, "columns": cols, "data": data}


def corr_to_payload(corr: pd.DataFrame) -> dict[str, Any]:
    matrix = df_to_records(corr)
    undefined: list[dict[str, str]] = []
    for i, a in enumerate(corr.index):
        for j, b in enumerate(corr.columns):
            if i <= j:
                continue
            val = corr.iloc[i, j] if hasattr(corr, "iloc") else corr.loc[a, b]
            if val is None or (isinstance(val, float) and not np.isfinite(val)):
                undefined.append({"a": str(a), "b": str(b), "status": "não definido"})
    return {"matrix": matrix, "undefined_pairs": undefined}


def series_map_to_payload(mapping: dict[str, pd.Series]) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for k, s in mapping.items():
        out[k] = {}
        for idx, val in s.items():
            key = str(idx.date()) if hasattr(idx, "date") else str(idx)
            if val is None or (isinstance(val, float) and not np.isfinite(val)):
                out[k][key] = None
            else:
                out[k][key] = float(val)
    return out


def result_summary(result: PipelineResult) -> dict[str, Any]:
    return {
        "analysis_id": result.metadata.analysis_id,
        "metadata": result.metadata.to_dict(),
        "quality": result.quality.to_dict(),
        "metrics": {k: v.to_dict() for k, v in result.metrics.items()},
        "correlation": corr_to_payload(result.correlation),
        "report_md": result.report_md,
        "returns": df_to_records(result.returns),
        "prices": df_to_records(result.prices),
        "individual_returns": series_map_to_payload(result.individual_returns),
        "drawdowns": series_map_to_payload(result.drawdowns),
        "units": {
            "returns": "decimal",
            "display_hint": "Multiplique por 100 para percentual",
            "prices": f"preço ajustado ({result.metadata.price_field})",
        },
    }
