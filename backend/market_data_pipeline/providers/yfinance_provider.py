"""Provedor yfinance com normalização de formatos e retentativas."""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from market_data_pipeline.config import PipelineConfig
from market_data_pipeline.exceptions import ProviderError
from market_data_pipeline.providers.base import PriceProvider, ProviderDownloadResult


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_yfinance_frame(
    data: pd.DataFrame | pd.Series,
    tickers: list[str],
    price_field: str = "Adj Close",
) -> dict[str, pd.Series]:
    """Normaliza respostas yfinance (Series, DataFrame simples ou MultiIndex).

    O yfinance pode retornar:
    - Series (1 ticker, 1 campo)
    - DataFrame com colunas OHLCV (1 ticker)
    - DataFrame MultiIndex (campo, ticker) ou (ticker, campo)
    """
    if data is None or (isinstance(data, pd.DataFrame) and data.empty) or (
        isinstance(data, pd.Series) and data.empty
    ):
        return {}

    result: dict[str, pd.Series] = {}

    if isinstance(data, pd.Series):
        ticker = tickers[0] if tickers else "UNKNOWN"
        s = data.copy()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        result[ticker] = s.astype(float)
        return result

    df = data.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)

    if isinstance(df.columns, pd.MultiIndex):
        # Detectar orientação: nível 0 = campos (Open, High, ...) ou tickers
        level0 = [str(x) for x in df.columns.get_level_values(0).unique()]
        ohlcv_like = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
        if any(x in ohlcv_like for x in level0):
            # (field, ticker)
            for ticker in tickers:
                try:
                    if price_field in df.columns.get_level_values(0):
                        series = df[price_field][ticker] if ticker in df[price_field].columns else None
                    else:
                        series = None
                except Exception:
                    series = None
                if series is None:
                    # tentar Close como fallback documentado
                    try:
                        series = df["Close"][ticker]
                    except Exception:
                        series = None
                if series is not None:
                    s = series.dropna()
                    if not s.empty:
                        result[ticker] = s.astype(float)
        else:
            # (ticker, field)
            for ticker in tickers:
                if ticker not in df.columns.get_level_values(0):
                    continue
                sub = df[ticker]
                col = price_field if price_field in sub.columns else ("Close" if "Close" in sub.columns else None)
                if col is None:
                    continue
                s = sub[col].dropna()
                if not s.empty:
                    result[ticker] = s.astype(float)
        return result

    # Colunas simples
    cols = [str(c) for c in df.columns]
    if price_field in cols:
        # Pode ser 1 ticker com OHLCV
        if len(tickers) == 1 and set(cols) & {"Open", "High", "Low", "Close", "Adj Close", "Volume"}:
            s = df[price_field].dropna()
            if not s.empty:
                result[tickers[0]] = s.astype(float)
            return result
        # Ou colunas = tickers com auto_adjust já aplicado (só Adj Close flatten)
    # Colunas = tickers (download com auto_adjust / group_by)
    for ticker in tickers:
        if ticker in df.columns:
            s = df[ticker].dropna()
            if isinstance(s, pd.DataFrame):
                col = price_field if price_field in s.columns else ("Close" if "Close" in s.columns else s.columns[0])
                s = s[col]
            s = s.dropna()
            if not s.empty:
                result[ticker] = s.astype(float)
        elif price_field in df.columns and len(tickers) == 1:
            s = df[price_field].dropna()
            if not s.empty:
                result[tickers[0]] = s.astype(float)

    # Última tentativa: se há exatamente as colunas OHLCV
    if not result and price_field in df.columns and len(tickers) >= 1:
        s = df[price_field].dropna()
        if not s.empty:
            result[tickers[0]] = s.astype(float)

    return result


class YFinanceProvider(PriceProvider):
    name = "yfinance"

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    def download(
        self,
        tickers: list[str],
        start: date,
        end: date,
    ) -> ProviderDownloadResult:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError(
                "Pacote yfinance não instalado. Instale as dependências do backend."
            ) from exc

        collected_at = _utcnow_iso()
        prices: dict[str, pd.Series] = {}
        failed: dict[str, str] = {}
        currencies: dict[str, str] = {}
        notes: list[str] = []

        # end exclusivo em yfinance: somar 1 dia para incluir end
        end_inclusive = end
        end_download = (pd.Timestamp(end) + pd.Timedelta(days=1)).date()

        last_error: Exception | None = None
        raw: Any = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                # timeout pode não existir em todas as versões do yfinance
                download_kwargs = dict(
                    tickers=tickers,
                    start=start.isoformat(),
                    end=end_download.isoformat(),
                    auto_adjust=False,  # usamos Adj Close explicitamente
                    progress=False,
                    threads=True,
                    group_by="column",
                )
                try:
                    raw = yf.download(**download_kwargs, timeout=self.config.download_timeout_s)
                except TypeError:
                    raw = yf.download(**download_kwargs)
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001 — retentativa documentada
                last_error = exc
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff_s * attempt)

        if last_error is not None and raw is None:
            raise ProviderError(
                f"Falha ao baixar dados do yfinance após {self.config.max_retries} tentativas: {last_error}",
                details={"error": str(last_error)},
            )

        notes.append(
            "Política: auto_adjust=False e campo Adj Close — evita ajuste duplicado."
        )
        notes.append(f"Intervalo solicitado inclusivo: {start.isoformat()} a {end_inclusive.isoformat()}.")

        parsed = normalize_yfinance_frame(raw, tickers, self.config.price_field)

        for ticker in tickers:
            series = parsed.get(ticker)
            if series is None or series.empty:
                failed[ticker] = "Resposta vazia ou ticker sem dados no intervalo."
                continue
            # Filtrar ao intervalo solicitado
            mask = (series.index.date >= start) & (series.index.date <= end)
            series = series.loc[mask]
            if series.empty:
                failed[ticker] = "Sem observações no intervalo após filtro de datas."
                continue
            prices[ticker] = series

            # Moeda best-effort (não bloqueia)
            try:
                info = yf.Ticker(ticker).fast_info
                cur = getattr(info, "currency", None) or (info.get("currency") if isinstance(info, dict) else None)
                if cur:
                    currencies[ticker] = str(cur)
            except Exception:
                currencies[ticker] = "BRL" if ticker.endswith(".SA") else "UNKNOWN"

        return ProviderDownloadResult(
            prices=prices,
            failed=failed,
            currencies=currencies,
            source="yfinance",
            collected_at=collected_at,
            raw_notes=notes,
        )
