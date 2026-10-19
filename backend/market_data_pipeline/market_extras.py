"""Complementos de mercado isolados — falhas não bloqueiam o pipeline histórico.

Consultas best-effort via yfinance. Não anunciam cotação em tempo real:
retornam a última cotação disponível com data/fonte quando possível.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_last_quote(ticker: str) -> dict[str, Any]:
    """Última cotação disponível (não garantida como tempo real)."""
    try:
        import yfinance as yf
    except ImportError:
        return {
            "available": False,
            "ticker": ticker,
            "error": "yfinance não instalado",
            "queried_at": _utcnow(),
        }

    try:
        t = yf.Ticker(ticker.strip().upper())
        # hist recente
        hist = t.history(period="5d", auto_adjust=False)
        if hist is None or hist.empty:
            return {
                "available": False,
                "ticker": ticker,
                "error": "Sem cotação disponível",
                "source": "yfinance",
                "queried_at": _utcnow(),
                "disclaimer": "Não é cotação em tempo real garantida.",
            }
        last = hist.iloc[-1]
        last_date = hist.index[-1]
        price = float(last.get("Close", last.iloc[0]))
        return {
            "available": True,
            "ticker": ticker.strip().upper(),
            "price": price,
            "currency": getattr(getattr(t, "fast_info", None), "currency", None),
            "as_of_date": str(getattr(last_date, "date", lambda: last_date)()),
            "as_of_datetime": str(last_date),
            "source": "yfinance",
            "field": "Close (última barra disponível no histórico recente)",
            "queried_at": _utcnow(),
            "disclaimer": (
                "Última cotação disponível via yfinance — "
                "não garantida como tempo real. Diferente dos preços Adj Close "
                "usados no cálculo histórico de retornos."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "ticker": ticker,
            "error": str(exc),
            "source": "yfinance",
            "queried_at": _utcnow(),
            "disclaimer": "Complemento indisponível; análise histórica não é afetada.",
        }


def get_fundamentals(ticker: str) -> dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError:
        return {"available": False, "ticker": ticker, "error": "yfinance não instalado", "queried_at": _utcnow()}

    try:
        t = yf.Ticker(ticker.strip().upper())
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}

        keys = [
            "longName",
            "sector",
            "industry",
            "marketCap",
            "trailingPE",
            "forwardPE",
            "priceToBook",
            "dividendYield",
            "currency",
            "exchange",
            "quoteType",
        ]
        data = {k: info.get(k) for k in keys if info.get(k) is not None}
        period = info.get("mostRecentQuarter") or info.get("lastFiscalYearEnd")
        if not data:
            return {
                "available": False,
                "ticker": ticker,
                "error": "Fundamentos não disponíveis para este ticker",
                "source": "yfinance.info",
                "queried_at": _utcnow(),
            }
        return {
            "available": True,
            "ticker": ticker.strip().upper(),
            "data": data,
            "period_hint": str(period) if period else None,
            "source": "yfinance.info",
            "queried_at": _utcnow(),
            "disclaimer": "Campos dependem do que o provedor expõe; podem estar defasados.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "ticker": ticker,
            "error": str(exc),
            "source": "yfinance",
            "queried_at": _utcnow(),
        }


def get_news(ticker: str, limit: int = 10) -> dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError:
        return {"available": False, "ticker": ticker, "items": [], "error": "yfinance não instalado", "queried_at": _utcnow()}

    try:
        t = yf.Ticker(ticker.strip().upper())
        raw = []
        try:
            raw = t.news or []
        except Exception:
            raw = []

        items = []
        for n in raw[:limit]:
            # Formato yfinance pode variar (content aninhado em versões recentes)
            content = n.get("content") if isinstance(n.get("content"), dict) else {}
            title = n.get("title") or content.get("title") or n.get("headline")
            pub = (
                n.get("publisher")
                or content.get("provider", {}).get("displayName")
                if isinstance(content.get("provider"), dict)
                else None
            ) or n.get("source")
            link = n.get("link") or content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else n.get("url")
            ts = n.get("providerPublishTime") or content.get("pubDate") or n.get("pubDate")
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            else:
                dt = str(ts) if ts else None
            if title:
                items.append(
                    {
                        "title": title,
                        "source": pub,
                        "date": dt,
                        "link": link,
                    }
                )

        if not items:
            return {
                "available": False,
                "ticker": ticker,
                "items": [],
                "error": "Nenhuma notícia disponível",
                "source": "yfinance.news",
                "queried_at": _utcnow(),
            }
        return {
            "available": True,
            "ticker": ticker.strip().upper(),
            "items": items,
            "source": "yfinance.news",
            "queried_at": _utcnow(),
            "disclaimer": "Notícias best-effort; indisponibilidade não afeta o pipeline histórico.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "ticker": ticker,
            "items": [],
            "error": str(exc),
            "source": "yfinance",
            "queried_at": _utcnow(),
        }
