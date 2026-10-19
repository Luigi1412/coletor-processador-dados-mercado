"""CLI compartilhando a mesma lógica da API."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from market_data_pipeline.config import (
    OFFICIAL_TICKERS,
    PipelineConfig,
    default_start_end,
)
from market_data_pipeline.exceptions import PipelineError
from market_data_pipeline.exports import export_all
from market_data_pipeline.persistence import save_analysis
from market_data_pipeline.pipeline import compute_daily_returns

app = typer.Typer(help="Coletor e Processador de Dados de Mercado — CLI")
console = Console()


@app.command("collect")
def collect(
    tickers: str = typer.Option(
        ",".join(OFFICIAL_TICKERS),
        "--tickers",
        "-t",
        help="Tickers separados por vírgula (carteira oficial por padrão)",
    ),
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Data inicial YYYY-MM-DD"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="Data final YYYY-MM-DD"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Diretório de saída"),
    allow_partial: bool = typer.Option(False, "--allow-partial", help="Analisar apenas ativos disponíveis"),
    data_dir: Path = typer.Option(Path("data/analyses"), "--data-dir", help="Persistência local"),
) -> None:
    """Coleta, trata e exporta retornos diários."""
    d0, d1 = default_start_end(2)
    start_s = start or d0.isoformat()
    end_s = end or d1.isoformat()
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]

    cfg = PipelineConfig(data_dir=str(data_dir))
    console.print(f"[bold]Coletando[/bold] {ticker_list} de {start_s} a {end_s}...")

    try:
        result = compute_daily_returns(
            ticker_list,
            start_s,
            end_s,
            allow_partial=allow_partial,
            config=cfg,
        )
    except PipelineError as exc:
        console.print(f"[red]Erro ({exc.code}):[/red] {exc.message}")
        if exc.details:
            console.print(exc.details)
        raise typer.Exit(code=1) from exc

    save_analysis(result, cfg)
    paths = export_all(result, output / result.metadata.analysis_id)

    console.print(f"[green]Análise[/green] {result.metadata.analysis_id}")
    console.print(result.preview(5))
    console.print(
        f"Dimensão: {result.returns.shape[0]} obs × {result.returns.shape[1]} ativos | "
        f"Período efetivo: {result.quality.effective_start} → {result.quality.effective_end}"
    )

    table = Table(title="Métricas (decimal)")
    table.add_column("Ativo")
    table.add_column("Média")
    table.add_column("Std")
    table.add_column("Min")
    table.add_column("Max")
    table.add_column("n")
    for t, m in result.metrics.items():
        table.add_row(
            t,
            f"{m.mean_daily:.6f}" if m.mean_daily is not None else "n/d",
            f"{m.std_daily:.6f}" if m.std_daily is not None else "n/d",
            f"{m.min_daily:.6f}" if m.min_daily is not None else "n/d",
            f"{m.max_daily:.6f}" if m.max_daily is not None else "n/d",
            str(m.n_observations),
        )
    console.print(table)
    console.print("Exportações:")
    for k, v in paths.items():
        console.print(f"  - {k}: {v}")
    console.print(f"Persistido em: {cfg.data_dir}/{result.metadata.analysis_id}")


@app.command("defaults")
def defaults() -> None:
    """Mostra tickers provisórios e período sugerido."""
    s, e = default_start_end(2)
    from market_data_pipeline.config import OFFICIAL_TEST_END, OFFICIAL_TEST_START

    console.print("Tickers oficiais do Grupo 4:", ", ".join(OFFICIAL_TICKERS))
    console.print(f"Período de teste oficial: {OFFICIAL_TEST_START} → {OFFICIAL_TEST_END}")
    console.print(f"Período UI (~2 anos até hoje): {s.isoformat()} → {e.isoformat()}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
