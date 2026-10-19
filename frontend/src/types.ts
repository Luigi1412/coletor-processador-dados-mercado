export interface FramePayload {
  index: string[];
  columns: string[];
  data: (number | null)[][];
}

export interface AssetMetrics {
  ticker: string;
  n_observations: number;
  mean_daily: number | null;
  std_daily: number | null;
  min_daily: number | null;
  max_daily: number | null;
  cumulative_return: number | null;
  max_drawdown: number | null;
  mean_is_historical_estimate: boolean;
}

export interface QualityReport {
  requested_start: string;
  requested_end: string;
  effective_start: string | null;
  effective_end: string | null;
  requested_tickers: string[];
  available_tickers: string[];
  unavailable_tickers: string[];
  aligned_dates_count: number;
  dates_removed_by_alignment: string[];
  alignment_coverage_ratio: number | null;
  gaps: { ticker: string; date: string; kind: string; detail: string }[];
  assets: {
    ticker: string;
    observations_raw: number;
    observations_after_dedup: number;
    observations_with_valid_returns: number;
    observations_aligned: number;
    duplicates_removed: number;
    unexpected_gaps: string[];
    available: boolean;
    failure_reason: string | null;
    currency: string | null;
  }[];
  source: string;
  collected_at: string;
  methodology_version: string;
  notes: string[];
  currencies: string[];
  mixed_currencies: boolean;
}

export interface AnalysisResult {
  analysis_id: string;
  metadata: {
    analysis_id: string;
    tickers: string[];
    start: string;
    end: string;
    allow_partial: boolean;
    provider: string;
    source: string;
    collected_at: string;
    methodology_version: string;
    parent_analysis_id: string | null;
    price_field: string;
  };
  quality: QualityReport;
  metrics: Record<string, AssetMetrics>;
  correlation: {
    matrix: FramePayload;
    undefined_pairs: { a: string; b: string; status: string }[];
  };
  report_md: string;
  returns: FramePayload;
  prices: FramePayload;
  individual_returns: Record<string, Record<string, number | null>>;
  drawdowns: Record<string, Record<string, number | null>>;
  units: {
    returns: string;
    display_hint: string;
    prices: string;
  };
}

export interface DefaultsConfig {
  provisional_tickers: string[];
  provisional_note: string;
  suggested_start: string;
  suggested_end: string;
  max_tickers: number;
  price_field: string;
  methodology_version: string;
}

export interface AnalysisListItem {
  analysis_id: string;
  tickers: string[];
  start: string;
  end: string;
  collected_at: string;
  methodology_version: string;
  parent_analysis_id?: string | null;
}

export type UiState =
  | "empty"
  | "loading"
  | "connection_error"
  | "invalid_ticker"
  | "partial"
  | "insufficient"
  | "loaded"
  | "exporting";
