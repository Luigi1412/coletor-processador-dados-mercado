"""Exportações CSV, Excel e Markdown."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_data_pipeline.pipeline import PipelineResult


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_prices_csv(result: PipelineResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = result.prices.copy()
    df.index.name = "date"
    df.to_csv(path, date_format="%Y-%m-%d")
    return path


def export_returns_csv(result: PipelineResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = result.returns.copy()
    df.index.name = "date"
    # Comentário de unidade via linha inicial? Mantemos CSV limpo + metadados no Excel
    df.to_csv(path, date_format="%Y-%m-%d")
    return path


def export_metrics_csv(result: PipelineResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [m.to_dict() for m in result.metrics.values()]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def export_report_md(result: PipelineResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"<!-- analysis_id={result.metadata.analysis_id} "
        f"methodology={result.metadata.methodology_version} "
        f"collected_at={result.metadata.collected_at} "
        f"unit_returns=decimal -->\n\n"
    )
    path.write_text(header + result.report_md, encoding="utf-8")
    return path


def export_excel(result: PipelineResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    prices = result.prices.copy()
    prices.index.name = "date"
    returns = result.returns.copy()
    returns.index.name = "date"
    metrics = pd.DataFrame([m.to_dict() for m in result.metrics.values()])
    corr = result.correlation.copy()
    quality_assets = pd.DataFrame([a.__dict__ for a in result.quality.assets])
    meta = pd.DataFrame([result.metadata.to_dict()])
    meta["returns_unit"] = "decimal (0.01 = 1%)"
    meta["price_field"] = result.metadata.price_field
    notes = pd.DataFrame({"notes": result.quality.notes})

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        prices.to_excel(writer, sheet_name="precos")
        returns.to_excel(writer, sheet_name="retornos")
        metrics.to_excel(writer, sheet_name="metricas", index=False)
        corr.to_excel(writer, sheet_name="correlacao")
        quality_assets.to_excel(writer, sheet_name="qualidade", index=False)
        meta.to_excel(writer, sheet_name="metadados", index=False)
        notes.to_excel(writer, sheet_name="notas", index=False)
    return path


def export_all(result: PipelineResult, output_dir: str | Path) -> dict[str, str]:
    """Gera todos os artefatos de exportação em um diretório."""
    out = _ensure_dir(Path(output_dir))
    paths = {
        "prices_csv": str(export_prices_csv(result, out / "precos_ajustados.csv")),
        "returns_csv": str(export_returns_csv(result, out / "retornos_diarios.csv")),
        "metrics_csv": str(export_metrics_csv(result, out / "metricas.csv")),
        "excel": str(export_excel(result, out / "analise.xlsx")),
        "report_md": str(export_report_md(result, out / "relatorio.md")),
    }
    return paths
