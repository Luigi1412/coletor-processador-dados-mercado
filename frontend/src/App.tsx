import { useEffect, useMemo, useState } from "react";
import { ApiError, api, getApiUrl } from "./api";
import { Base100Chart, DrawdownChart, PriceChart, RiskReturnScatter } from "./charts";
import { dateBr, datetimeBr, pct } from "./format";
import type { AnalysisListItem, AnalysisResult, DefaultsConfig, UiState } from "./types";
import "./App.css";

type Tab = "qualidade" | "metricas" | "graficos" | "correlacao" | "relatorio" | "complementos" | "exportar";

export default function App() {
  const [defaults, setDefaults] = useState<DefaultsConfig | null>(null);
  const [tickersInput, setTickersInput] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [allowPartial, setAllowPartial] = useState(false);
  const [state, setState] = useState<UiState>("empty");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [partialInfo, setPartialInfo] = useState<{ failed: string[]; available: string[] } | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisListItem[]>([]);
  const [tab, setTab] = useState<Tab>("qualidade");
  const [sortKey, setSortKey] = useState<string>("ticker");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [extraTicker, setExtraTicker] = useState("");
  const [extras, setExtras] = useState<{
    quote?: Record<string, unknown>;
    fundamentals?: Record<string, unknown>;
    news?: Record<string, unknown>;
  }>({});
  const [extrasLoading, setExtrasLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        await api.health();
        const d = await api.defaults();
        setDefaults(d);
        setTickersInput(d.provisional_tickers.slice(0, 3).join(", "));
        setStart(d.suggested_start);
        setEnd(d.suggested_end);
        setHistory(await api.list());
      } catch (e) {
        setState("connection_error");
        setErrorMsg(e instanceof ApiError ? e.message : "Falha ao conectar.");
      }
    })();
  }, []);

  const parsedTickers = useMemo(
    () =>
      tickersInput
        .split(/[,;\s]+/)
        .map((t) => t.trim().toUpperCase())
        .filter(Boolean),
    [tickersInput],
  );

  async function runCollect(forcePartial = allowPartial) {
    setState("loading");
    setErrorMsg(null);
    setPartialInfo(null);
    try {
      const data = await api.create({
        tickers: parsedTickers,
        start,
        end,
        allow_partial: forcePartial,
      });
      setResult(data);
      setState(data.quality.unavailable_tickers.length ? "partial" : "loaded");
      setTab("qualidade");
      setHistory(await api.list());
      setExtraTicker(data.quality.available_tickers[0] || "");
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.code === "connection_error") {
          setState("connection_error");
        } else if (e.code === "partial_failure") {
          setState("partial");
          const details = e.details as { failed?: string[]; available?: string[] } | undefined;
          setPartialInfo({
            failed: details?.failed || [],
            available: details?.available || [],
          });
        } else if (e.code === "insufficient_data") {
          setState("insufficient");
        } else if (e.code === "validation_error") {
          setState("invalid_ticker");
        } else {
          setState("invalid_ticker");
        }
        setErrorMsg(e.message);
        setResult(null);
      } else {
        setState("connection_error");
        setErrorMsg("Erro inesperado.");
      }
    }
  }

  async function openAnalysis(id: string) {
    setState("loading");
    try {
      const data = await api.get(id);
      setResult(data);
      setState("loaded");
      setTickersInput(data.metadata.tickers.join(", "));
      setStart(data.metadata.start);
      setEnd(data.metadata.end);
      setTab("qualidade");
      setExtraTicker(data.quality.available_tickers[0] || "");
    } catch (e) {
      setState("connection_error");
      setErrorMsg(e instanceof ApiError ? e.message : "Falha ao reabrir.");
    }
  }

  async function refreshAnalysis() {
    if (!result) return;
    setState("loading");
    try {
      const data = await api.refresh(result.analysis_id, allowPartial);
      setResult(data);
      setState("loaded");
      setHistory(await api.list());
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Falha na atualização.");
      setState("loaded");
    }
  }

  async function loadExtras() {
    if (!extraTicker) return;
    setExtrasLoading(true);
    try {
      const [quote, fundamentals, news] = await Promise.all([
        api.quote(extraTicker),
        api.fundamentals(extraTicker),
        api.news(extraTicker),
      ]);
      setExtras({ quote, fundamentals, news });
    } catch {
      setExtras({
        quote: { available: false, error: "Complemento indisponível" },
        fundamentals: { available: false, error: "Complemento indisponível" },
        news: { available: false, error: "Complemento indisponível", items: [] },
      });
    } finally {
      setExtrasLoading(false);
    }
  }

  const sortedMetrics = useMemo(() => {
    if (!result) return [];
    const rows = Object.values(result.metrics);
    const dir = sortDir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sortKey];
      const bv = (b as unknown as Record<string, unknown>)[sortKey];
      if (typeof av === "string" && typeof bv === "string") return av.localeCompare(bv) * dir;
      if (av == null) return 1;
      if (bv == null) return -1;
      return ((av as number) - (bv as number)) * dir;
    });
  }, [result, sortKey, sortDir]);

  function toggleSort(key: string) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Portfolio Solutions · Wealth Management</p>
          <h1>Coletor e Processador de Dados de Mercado</h1>
          <p className="subtitle">
            Fundamento de preços ajustados e retornos diários · Inteli × BTG Pactual · Grupo 4
            <span className="badge">Protótipo acadêmico</span>
          </p>
        </div>
        <div className="api-pill">API: {getApiUrl()}</div>
      </header>

      <main className="layout">
        <aside className="panel form-panel">
          <h2>Nova análise</h2>
          {defaults && <p className="muted small">{defaults.provisional_note}</p>}
          <label>
            Ativos (separados por vírgula)
            <textarea
              value={tickersInput}
              onChange={(e) => setTickersInput(e.target.value)}
              rows={3}
              placeholder="PETR4.SA, VALE3.SA"
            />
          </label>
          <div className="row">
            <label>
              Início
              <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
            </label>
            <label>
              Fim
              <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
            </label>
          </div>
          <label className="check">
            <input type="checkbox" checked={allowPartial} onChange={(e) => setAllowPartial(e.target.checked)} />
            Permitir análise parcial (apenas ativos disponíveis)
          </label>
          <button className="primary" disabled={state === "loading" || !parsedTickers.length} onClick={() => runCollect()}>
            {state === "loading" ? "Coletando…" : "Iniciar coleta"}
          </button>

          {errorMsg && (
            <div className={`alert ${state === "partial" ? "warn" : "error"}`}>
              <strong>
                {state === "connection_error" && "Falha de conexão"}
                {state === "invalid_ticker" && "Entrada inválida"}
                {state === "partial" && "Coleta parcial"}
                {state === "insufficient" && "Dados insuficientes"}
                {!["connection_error", "invalid_ticker", "partial", "insufficient"].includes(state) && "Atenção"}
              </strong>
              <p>{errorMsg}</p>
              {partialInfo && (
                <div className="partial-actions">
                  <p>Disponíveis: {partialInfo.available.join(", ") || "—"}</p>
                  <p>Falhos: {partialInfo.failed.join(", ") || "—"}</p>
                  <button
                    className="secondary"
                    onClick={() => {
                      setAllowPartial(true);
                      setTickersInput(partialInfo.available.join(", "));
                      runCollect(true);
                    }}
                  >
                    Analisar apenas os disponíveis
                  </button>
                </div>
              )}
            </div>
          )}

          <h2 className="mt">Análises anteriores</h2>
          <ul className="history">
            {history.length === 0 && <li className="muted">Nenhuma análise salva.</li>}
            {history.slice(0, 12).map((h) => (
              <li key={h.analysis_id}>
                <button className="linkish" onClick={() => openAnalysis(h.analysis_id)}>
                  <span>{h.tickers.join(", ")}</span>
                  <small>
                    {dateBr(h.start)} – {dateBr(h.end)} · {datetimeBr(h.collected_at)}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="panel results">
          {state === "empty" && !result && (
            <div className="empty-state">
              <h2>Nenhuma análise carregada</h2>
              <p>
                Selecione ativos e o período (padrão sugerido: ~2 anos), inicie a coleta e explore cobertura,
                métricas e gráficos. Retornos internos em decimal; exibição em percentual (pt-BR).
              </p>
            </div>
          )}

          {state === "loading" && (
            <div className="empty-state">
              <div className="spinner" />
              <h2>Processando coleta</h2>
              <p>Download, tratamento de lacunas, alinhamento e cálculo de métricas…</p>
            </div>
          )}

          {state === "connection_error" && !result && (
            <div className="empty-state">
              <h2>Backend indisponível</h2>
              <p>{errorMsg}</p>
              <p className="muted">Inicie a API: <code>uvicorn market_data_pipeline.api:app --reload</code></p>
            </div>
          )}

          {result && (
            <>
              <div className="result-header">
                <div>
                  <h2>Análise {result.analysis_id.slice(0, 8)}…</h2>
                  <p className="muted">
                    Solicitado {dateBr(result.quality.requested_start)} – {dateBr(result.quality.requested_end)} ·
                    Efetivo {dateBr(result.quality.effective_start)} – {dateBr(result.quality.effective_end)} ·{" "}
                    {result.quality.aligned_dates_count} obs alinhadas · Fonte {result.quality.source} ·{" "}
                    {datetimeBr(result.quality.collected_at)}
                  </p>
                  {result.quality.mixed_currencies && (
                    <p className="warn-inline">Moedas distintas — sem conversão para moeda comum.</p>
                  )}
                </div>
                <button className="secondary" onClick={refreshAnalysis}>
                  Atualizar manualmente
                </button>
              </div>

              <nav className="tabs">
                {(
                  [
                    ["qualidade", "Cobertura"],
                    ["metricas", "Métricas"],
                    ["graficos", "Gráficos"],
                    ["correlacao", "Correlação"],
                    ["relatorio", "Relatório"],
                    ["complementos", "Complementos"],
                    ["exportar", "Exportar"],
                  ] as [Tab, string][]
                ).map(([id, label]) => (
                  <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
                    {label}
                  </button>
                ))}
              </nav>

              {tab === "qualidade" && (
                <div className="block">
                  <h3>Qualidade e procedência</h3>
                  <p className="muted small">
                    Cobertura das séries individuais ≠ amostra comum usada nas estatísticas comparativas.
                    Retornos não atravessam lacunas inesperadas.
                  </p>
                  <table>
                    <thead>
                      <tr>
                        <th>Ativo</th>
                        <th>Bruto</th>
                        <th>Pós-dedup</th>
                        <th>Retornos válidos</th>
                        <th>Alinhado</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.quality.assets.map((a) => (
                        <tr key={a.ticker}>
                          <td>{a.ticker}</td>
                          <td>{a.observations_raw}</td>
                          <td>{a.observations_after_dedup}</td>
                          <td>{a.observations_with_valid_returns}</td>
                          <td>{a.observations_aligned}</td>
                          <td>{a.available ? "OK" : a.failure_reason || "indisponível"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {result.quality.unavailable_tickers.length > 0 && (
                    <p className="alert warn">Ativos indisponíveis: {result.quality.unavailable_tickers.join(", ")}</p>
                  )}
                  <p>
                    Datas removidas no alinhamento: {result.quality.dates_removed_by_alignment.length} · Cobertura:{" "}
                    {result.quality.alignment_coverage_ratio != null
                      ? pct(result.quality.alignment_coverage_ratio)
                      : "n/d"}
                  </p>
                  {result.quality.notes.map((n) => (
                    <p key={n} className="muted small">
                      · {n}
                    </p>
                  ))}
                </div>
              )}

              {tab === "metricas" && (
                <div className="block">
                  <h3>Métricas por ativo</h3>
                  <p className="muted small">
                    Valores internos em decimal. Exibição em %. Média = estimativa histórica do retorno esperado
                    diário — não é previsão.
                  </p>
                  <table>
                    <thead>
                      <tr>
                        {[
                          ["ticker", "Ativo"],
                          ["mean_daily", "Média"],
                          ["std_daily", "Desvio"],
                          ["min_daily", "Mín"],
                          ["max_daily", "Máx"],
                          ["cumulative_return", "Acumulado"],
                          ["max_drawdown", "Max DD"],
                          ["n_observations", "n"],
                        ].map(([k, label]) => (
                          <th key={k}>
                            <button className="th-btn" onClick={() => toggleSort(k)}>
                              {label}
                            </button>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedMetrics.map((m) => (
                        <tr key={m.ticker}>
                          <td>{m.ticker}</td>
                          <td>{pct(m.mean_daily, 3)}</td>
                          <td>{pct(m.std_daily, 3)}</td>
                          <td>{pct(m.min_daily)}</td>
                          <td>{pct(m.max_daily)}</td>
                          <td>{pct(m.cumulative_return)}</td>
                          <td>{pct(m.max_drawdown)}</td>
                          <td>{m.n_observations}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {tab === "graficos" && (
                <div className="charts-grid">
                  <PriceChart prices={result.prices} />
                  <Base100Chart prices={result.prices} />
                  <DrawdownChart result={result} />
                  <RiskReturnScatter metrics={result.metrics} />
                </div>
              )}

              {tab === "correlacao" && (
                <div className="block">
                  <h3>Matriz de correlação (Pearson)</h3>
                  <p className="muted small">Pares indefinidos (série constante / amostra insuficiente) → “não definido”.</p>
                  <table>
                    <thead>
                      <tr>
                        <th></th>
                        {result.correlation.matrix.columns.map((c) => (
                          <th key={c}>{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.correlation.matrix.columns.map((row, i) => (
                        <tr key={row}>
                          <th>{row}</th>
                          {result.correlation.matrix.data[i]?.map((v, j) => (
                            <td key={j}>{v === null || Number.isNaN(v) ? "não definido" : v.toFixed(3).replace(".", ",")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {result.correlation.undefined_pairs.length > 0 && (
                    <ul className="muted small">
                      {result.correlation.undefined_pairs.map((p) => (
                        <li key={`${p.a}-${p.b}`}>
                          {p.a} × {p.b}: {p.status}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {tab === "relatorio" && (
                <div className="block report">
                  <pre>{result.report_md}</pre>
                </div>
              )}

              {tab === "complementos" && (
                <div className="block">
                  <h3>Complementos de mercado</h3>
                  <p className="muted small">
                    Isolados do pipeline histórico. Indisponibilidade não invalida a análise de retornos.
                  </p>
                  <div className="row">
                    <input value={extraTicker} onChange={(e) => setExtraTicker(e.target.value.toUpperCase())} />
                    <button className="secondary" onClick={loadExtras} disabled={extrasLoading}>
                      {extrasLoading ? "Consultando…" : "Consultar"}
                    </button>
                  </div>
                  {!extras.quote && <p className="muted">Nenhuma consulta ainda.</p>}
                  {extras.quote && (
                    <div className="extras">
                      <article>
                        <h4>Última cotação disponível</h4>
                        {extras.quote.available ? (
                          <>
                            <p>
                              {String(extras.quote.price)} ({String(extras.quote.currency || "—")}) em{" "}
                              {String(extras.quote.as_of_date)}
                            </p>
                            <p className="muted small">{String(extras.quote.disclaimer)}</p>
                          </>
                        ) : (
                          <p className="alert warn">Indisponível: {String(extras.quote.error || "—")}</p>
                        )}
                      </article>
                      <article>
                        <h4>Fundamentos</h4>
                        {extras.fundamentals?.available ? (
                          <pre className="tiny">{JSON.stringify(extras.fundamentals.data, null, 2)}</pre>
                        ) : (
                          <p className="alert warn">Indisponível: {String(extras.fundamentals?.error || "—")}</p>
                        )}
                      </article>
                      <article>
                        <h4>Notícias</h4>
                        {extras.news?.available ? (
                          <ul>
                            {((extras.news.items as { title: string; source?: string; date?: string; link?: string }[]) || []).map(
                              (n, i) => (
                                <li key={i}>
                                  {n.link ? (
                                    <a href={n.link} target="_blank" rel="noreferrer">
                                      {n.title}
                                    </a>
                                  ) : (
                                    n.title
                                  )}
                                  <small>
                                    {" "}
                                    · {n.source || "—"} · {n.date || "—"}
                                  </small>
                                </li>
                              ),
                            )}
                          </ul>
                        ) : (
                          <p className="alert warn">Indisponível: {String(extras.news?.error || "—")}</p>
                        )}
                      </article>
                    </div>
                  )}
                </div>
              )}

              {tab === "exportar" && (
                <div className="block">
                  <h3>Exportações</h3>
                  <p className="muted small">
                    Correspondem à análise exibida. Excel desta aplicação não substitui automaticamente o artefato de
                    planilha.
                  </p>
                  <div className="export-grid">
                    {[
                      ["csv_prices", "CSV preços ajustados"],
                      ["csv_returns", "CSV retornos diários"],
                      ["csv_metrics", "CSV métricas"],
                      ["xlsx", "Excel (abas)"],
                      ["md", "Relatório Markdown"],
                    ].map(([fmt, label]) => (
                      <a key={fmt} className="export-btn" href={api.exportUrl(result.analysis_id, fmt)}>
                        {label}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </main>

      <footer className="footer">
        Metodologia {defaults?.methodology_version || "1.0.0"} · Preço: Adj Close · Retorno simples diário · Grupo 4 —
        protótipo acadêmico (não é produto oficial BTG)
      </footer>
    </div>
  );
}
