"""Persistência local de análises."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.exceptions import PipelineError
from market_data_pipeline.models import AnalysisMetadata, AssetMetrics, QualityReport
from market_data_pipeline.pipeline import PipelineResult


def _root(config: PipelineConfig | None = None) -> Path:
    cfg = config or PipelineConfig()
    root = Path(cfg.data_dir)
    if not root.is_absolute():
        # Relativo ao cwd; a API define cwd/data
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def analysis_dir(analysis_id: str, config: PipelineConfig | None = None) -> Path:
    return _root(config) / analysis_id


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Não serializável: {type(obj)}")


def save_analysis(result: PipelineResult, config: PipelineConfig | None = None) -> Path:
    """Salva coleta e resultados; retorna o diretório da análise."""
    d = analysis_dir(result.metadata.analysis_id, config)
    d.mkdir(parents=True, exist_ok=True)
    (d / "exports").mkdir(exist_ok=True)

    with open(d / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(result.metadata.to_dict(), f, ensure_ascii=False, indent=2)

    result.returns.to_parquet(d / "returns.parquet")
    result.prices.to_parquet(d / "prices.parquet")

    # Séries individuais e drawdowns
    indiv = {k: v.to_dict() for k, v in result.individual_returns.items()}
    # to_dict com timestamp keys
    indiv_ser: dict[str, dict[str, float]] = {}
    for k, s in result.individual_returns.items():
        indiv_ser[k] = {str(idx.date()): float(val) for idx, val in s.items()}
    with open(d / "individual_returns.json", "w", encoding="utf-8") as f:
        json.dump(indiv_ser, f, ensure_ascii=False, indent=2)

    dd_ser: dict[str, dict[str, float]] = {}
    for k, s in result.drawdowns.items():
        dd_ser[k] = {str(idx.date()): float(val) for idx, val in s.items()}
    with open(d / "drawdowns.json", "w", encoding="utf-8") as f:
        json.dump(dd_ser, f, ensure_ascii=False, indent=2)

    metrics_payload = {k: v.to_dict() for k, v in result.metrics.items()}
    with open(d / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, ensure_ascii=False, indent=2)

    corr = result.correlation.copy()
    # NaN → null
    with open(d / "correlation.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(corr.to_json(orient="split", date_format="iso")), f, indent=2)

    with open(d / "quality.json", "w", encoding="utf-8") as f:
        json.dump(result.quality.to_dict(), f, ensure_ascii=False, indent=2, default=_json_default)

    with open(d / "report.md", "w", encoding="utf-8") as f:
        f.write(result.report_md)

    return d


def list_analyses(config: PipelineConfig | None = None) -> list[dict[str, Any]]:
    root = _root(config)
    items: list[dict[str, Any]] = []
    for p in sorted(root.iterdir(), reverse=True):
        meta = p / "metadata.json"
        if p.is_dir() and meta.exists():
            with open(meta, encoding="utf-8") as f:
                items.append(json.load(f))
    return items


def load_analysis(analysis_id: str, config: PipelineConfig | None = None) -> PipelineResult:
    d = analysis_dir(analysis_id, config)
    if not d.exists():
        raise PipelineError(f"Análise não encontrada: {analysis_id}", code="not_found")

    with open(d / "metadata.json", encoding="utf-8") as f:
        meta_raw = json.load(f)
    metadata = AnalysisMetadata(**{k: v for k, v in meta_raw.items() if k in AnalysisMetadata.__dataclass_fields__})

    returns = pd.read_parquet(d / "returns.parquet")
    prices = pd.read_parquet(d / "prices.parquet")

    with open(d / "metrics.json", encoding="utf-8") as f:
        metrics_raw = json.load(f)
    metrics = {k: AssetMetrics(**v) for k, v in metrics_raw.items()}

    with open(d / "quality.json", encoding="utf-8") as f:
        quality_raw = json.load(f)
    # Reconstruir QualityReport de forma tolerante
    from market_data_pipeline.models import GapRecord, AssetQuality

    gaps = [GapRecord(**g) for g in quality_raw.get("gaps", [])]
    assets = [AssetQuality(**a) for a in quality_raw.get("assets", [])]
    quality = QualityReport(
        requested_start=quality_raw["requested_start"],
        requested_end=quality_raw["requested_end"],
        effective_start=quality_raw.get("effective_start"),
        effective_end=quality_raw.get("effective_end"),
        requested_tickers=quality_raw.get("requested_tickers", []),
        available_tickers=quality_raw.get("available_tickers", []),
        unavailable_tickers=quality_raw.get("unavailable_tickers", []),
        aligned_dates_count=quality_raw.get("aligned_dates_count", 0),
        dates_removed_by_alignment=quality_raw.get("dates_removed_by_alignment", []),
        alignment_coverage_ratio=quality_raw.get("alignment_coverage_ratio"),
        gaps=gaps,
        assets=assets,
        source=quality_raw.get("source", ""),
        collected_at=quality_raw.get("collected_at", ""),
        methodology_version=quality_raw.get("methodology_version", ""),
        notes=quality_raw.get("notes", []),
        currencies=quality_raw.get("currencies", []),
        mixed_currencies=quality_raw.get("mixed_currencies", False),
    )

    with open(d / "correlation.json", encoding="utf-8") as f:
        corr_raw = json.load(f)
    correlation = pd.DataFrame(**corr_raw) if "data" in corr_raw else pd.read_json(json.dumps(corr_raw), orient="split")

    with open(d / "report.md", encoding="utf-8") as f:
        report_md = f.read()

    individual_returns: dict[str, pd.Series] = {}
    ir_path = d / "individual_returns.json"
    if ir_path.exists():
        with open(ir_path, encoding="utf-8") as f:
            ir = json.load(f)
        for k, mapping in ir.items():
            individual_returns[k] = pd.Series(mapping)
            individual_returns[k].index = pd.to_datetime(individual_returns[k].index)

    drawdowns: dict[str, pd.Series] = {}
    dd_path = d / "drawdowns.json"
    if dd_path.exists():
        with open(dd_path, encoding="utf-8") as f:
            dd = json.load(f)
        for k, mapping in dd.items():
            drawdowns[k] = pd.Series(mapping)
            drawdowns[k].index = pd.to_datetime(drawdowns[k].index)

    return PipelineResult(
        returns=returns,
        prices=prices,
        individual_returns=individual_returns,
        drawdowns=drawdowns,
        quality=quality,
        metrics=metrics,
        correlation=correlation,
        report_md=report_md,
        metadata=metadata,
    )
