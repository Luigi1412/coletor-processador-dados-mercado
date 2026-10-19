import type { AnalysisListItem, AnalysisResult, DefaultsConfig } from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError("Falha de conexão com a API. Verifique se o backend está em execução.", 0, "connection_error");
  }

  if (!res.ok) {
    let payload: { message?: string; code?: string; details?: unknown; detail?: unknown } = {};
    try {
      payload = await res.json();
    } catch {
      /* ignore */
    }
    const detail = payload.detail as { message?: string; code?: string; details?: unknown } | string | undefined;
    const message =
      (typeof detail === "object" && detail?.message) ||
      payload.message ||
      (typeof detail === "string" ? detail : null) ||
      res.statusText;
    const code = (typeof detail === "object" && detail?.code) || payload.code;
    const details = (typeof detail === "object" && detail?.details) || payload.details;
    throw new ApiError(String(message), res.status, code, details);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return (await res.text()) as T;
}

export function getApiUrl() {
  return API_URL;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  defaults: () => request<DefaultsConfig>("/config/defaults"),
  list: () => request<AnalysisListItem[]>("/analyses"),
  create: (body: {
    tickers: string[];
    start: string;
    end: string;
    allow_partial: boolean;
  }) =>
    request<AnalysisResult>("/analyses", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  get: (id: string) => request<AnalysisResult>(`/analyses/${id}`),
  refresh: (id: string, allow_partial = false) =>
    request<AnalysisResult>(`/analyses/${id}/refresh?allow_partial=${allow_partial}`, { method: "POST" }),
  quote: (ticker: string) => request<Record<string, unknown>>(`/market/quote/${encodeURIComponent(ticker)}`),
  fundamentals: (ticker: string) =>
    request<Record<string, unknown>>(`/market/fundamentals/${encodeURIComponent(ticker)}`),
  news: (ticker: string) => request<Record<string, unknown>>(`/market/news/${encodeURIComponent(ticker)}`),
  exportUrl: (id: string, fmt: string) => `${API_URL}/analyses/${id}/export/${fmt}`,
};
