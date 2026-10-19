"""API FastAPI — mesma lógica do núcleo/CLI."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from market_data_pipeline.config import (
    METHODOLOGY_VERSION,
    OFFICIAL_TEST_END,
    OFFICIAL_TEST_START,
    OFFICIAL_TICKERS,
    PipelineConfig,
    default_start_end,
)
from market_data_pipeline.exceptions import PartialFailureError, PipelineError
from market_data_pipeline.exports import (
    export_excel,
    export_metrics_csv,
    export_prices_csv,
    export_report_md,
    export_returns_csv,
)
from market_data_pipeline.market_extras import get_fundamentals, get_last_quote, get_news
from market_data_pipeline.persistence import list_analyses, load_analysis, save_analysis
from market_data_pipeline.pipeline import compute_daily_returns
from market_data_pipeline.providers.csv_provider import (
    load_external_csv,
    transform_series_to_daily_returns,
)
from market_data_pipeline.serialization import result_summary

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "analyses"
CONFIG = PipelineConfig(data_dir=str(DATA_ROOT))

app = FastAPI(
    title="Coletor e Processador de Dados de Mercado",
    description="API do artefato Sprint 1 — Inteli × BTG Pactual — Grupo 4",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, examples=[["PETR4.SA", "VALE3.SA"]])
    start: str = Field(..., examples=["2024-01-01"])
    end: str = Field(..., examples=["2025-12-31"])
    allow_partial: bool = False
    provider: str = "yfinance"


class AnalysisListItem(BaseModel):
    analysis_id: str
    tickers: list[str]
    start: str
    end: str
    collected_at: str
    methodology_version: str
    parent_analysis_id: str | None = None


def _http_error(exc: PipelineError) -> HTTPException:
    status = 400
    if exc.code == "not_found":
        status = 404
    elif exc.code == "partial_failure":
        status = 409
    elif exc.code in ("insufficient_data", "provider_error"):
        status = 422
    return HTTPException(status_code=status, detail={"message": exc.message, "code": exc.code, "details": exc.details})


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "methodology_version": METHODOLOGY_VERSION}


@app.get("/config/defaults")
def config_defaults() -> dict[str, Any]:
    s, e = default_start_end(2)
    return {
        "provisional_tickers": OFFICIAL_TICKERS,
        "official_tickers": OFFICIAL_TICKERS,
        "provisional_note": (
            "Carteira oficial do Grupo 4 (PETR4, VALE3, ITUB4, WEGE3, ABEV3). "
            f"Período de teste documentado: {OFFICIAL_TEST_START} → {OFFICIAL_TEST_END}."
        ),
        "suggested_start": OFFICIAL_TEST_START,
        "suggested_end": OFFICIAL_TEST_END,
        "ui_default_start": s.isoformat(),
        "ui_default_end": e.isoformat(),
        "max_tickers": CONFIG.max_tickers,
        "price_field": CONFIG.price_field,
        "methodology_version": METHODOLOGY_VERSION,
    }


@app.post("/analyses")
def create_analysis(body: AnalysisRequest) -> dict[str, Any]:
    try:
        result = compute_daily_returns(
            body.tickers,
            body.start,
            body.end,
            provider=body.provider,
            allow_partial=body.allow_partial,
            config=CONFIG,
        )
        save_analysis(result, CONFIG)
        return result_summary(result)
    except PartialFailureError as exc:
        raise _http_error(exc) from exc
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.get("/analyses")
def get_analyses() -> list[dict[str, Any]]:
    return list_analyses(CONFIG)


@app.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str) -> dict[str, Any]:
    try:
        result = load_analysis(analysis_id, CONFIG)
        return result_summary(result)
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.post("/analyses/{analysis_id}/refresh")
def refresh_analysis(
    analysis_id: str,
    allow_partial: bool = Query(False),
) -> dict[str, Any]:
    """Nova coleta vinculada à análise anterior (preserva a versão antiga)."""
    try:
        old = load_analysis(analysis_id, CONFIG)
        result = compute_daily_returns(
            old.metadata.tickers,
            old.metadata.start,
            old.metadata.end,
            allow_partial=allow_partial or old.metadata.allow_partial,
            config=CONFIG,
            parent_analysis_id=analysis_id,
        )
        save_analysis(result, CONFIG)
        return result_summary(result)
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.get("/analyses/{analysis_id}/series")
def get_series(analysis_id: str) -> dict[str, Any]:
    try:
        result = load_analysis(analysis_id, CONFIG)
        summary = result_summary(result)
        return {
            "returns": summary["returns"],
            "prices": summary["prices"],
            "individual_returns": summary["individual_returns"],
            "drawdowns": summary["drawdowns"],
            "units": summary["units"],
        }
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.get("/analyses/{analysis_id}/metrics")
def get_metrics(analysis_id: str) -> dict[str, Any]:
    try:
        result = load_analysis(analysis_id, CONFIG)
        summary = result_summary(result)
        return {"metrics": summary["metrics"], "correlation": summary["correlation"]}
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.get("/analyses/{analysis_id}/quality")
def get_quality(analysis_id: str) -> dict[str, Any]:
    try:
        result = load_analysis(analysis_id, CONFIG)
        return result.quality.to_dict()
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.get("/analyses/{analysis_id}/report")
def get_report(analysis_id: str) -> PlainTextResponse:
    try:
        result = load_analysis(analysis_id, CONFIG)
        return PlainTextResponse(result.report_md, media_type="text/markdown; charset=utf-8")
    except PipelineError as exc:
        raise _http_error(exc) from exc


ExportFmt = Literal["csv_prices", "csv_returns", "csv_metrics", "xlsx", "md"]


@app.get("/analyses/{analysis_id}/export/{fmt}")
def export_analysis(analysis_id: str, fmt: ExportFmt) -> FileResponse:
    try:
        result = load_analysis(analysis_id, CONFIG)
        export_dir = Path(CONFIG.data_dir) / analysis_id / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        if fmt == "csv_prices":
            path = export_prices_csv(result, export_dir / "precos_ajustados.csv")
            media = "text/csv"
        elif fmt == "csv_returns":
            path = export_returns_csv(result, export_dir / "retornos_diarios.csv")
            media = "text/csv"
        elif fmt == "csv_metrics":
            path = export_metrics_csv(result, export_dir / "metricas.csv")
            media = "text/csv"
        elif fmt == "xlsx":
            path = export_excel(result, export_dir / "analise.xlsx")
            media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            path = export_report_md(result, export_dir / "relatorio.md")
            media = "text/markdown"
        return FileResponse(path, media_type=media, filename=path.name)
    except PipelineError as exc:
        raise _http_error(exc) from exc


@app.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    ticker: str = Form(...),
    series_type: str = Form(...),
    unit: str = Form("decimal"),
    frequency: str = Form("daily"),
    currency: str = Form("BRL"),
    source: str = Form("csv_upload"),
) -> dict[str, Any]:
    """Importa CSV externo validado. Não bloqueia o núcleo yfinance."""
    try:
        raw = await file.read()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = tmp.name
        series, meta = load_external_csv(
            tmp_path,
            ticker=ticker.strip().upper(),
            series_type=series_type,  # type: ignore[arg-type]
            unit=unit,
            frequency=frequency,
            currency=currency,
            source=source,
            config=CONFIG,
        )
        returns = transform_series_to_daily_returns(
            series, series_type, CONFIG.business_days_per_year  # type: ignore[arg-type]
        )
        Path(tmp_path).unlink(missing_ok=True)
        return {
            "ok": True,
            "meta": meta,
            "n_values": int(len(series)),
            "n_returns": int(len(returns)),
            "preview_returns": {str(i.date()): float(v) for i, v in list(returns.tail(5).items())},
            "note": (
                "Importação CSV para apoio ao artefato de planilha. "
                "Taxas CDI não são apresentadas como preço de ativo."
            ),
        }
    except PipelineError as exc:
        raise _http_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail={"message": str(exc), "code": "csv_import_error"}) from exc


@app.get("/market/quote/{ticker}")
def market_quote(ticker: str) -> dict[str, Any]:
    return get_last_quote(ticker)


@app.get("/market/fundamentals/{ticker}")
def market_fundamentals(ticker: str) -> dict[str, Any]:
    return get_fundamentals(ticker)


@app.get("/market/news/{ticker}")
def market_news(ticker: str, limit: int = Query(10, ge=1, le=50)) -> dict[str, Any]:
    return get_news(ticker, limit=limit)
