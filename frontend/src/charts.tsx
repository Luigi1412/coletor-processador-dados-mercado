import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { AnalysisResult, AssetMetrics, FramePayload } from "./types";
import { pct } from "./format";

const PALETTE = ["#003366", "#0A4D8C", "#1A6BB5", "#5A7A94", "#8FA3B5", "#C45C26", "#2E7D4F"];

function frameToSeries(frame: FramePayload): Record<string, string | number | null>[] {
  return frame.index.map((date, i) => {
    const row: Record<string, string | number | null> = { date };
    frame.columns.forEach((col, j) => {
      row[col] = frame.data[i]?.[j] ?? null;
    });
    return row;
  });
}

function pricesToBase100(frame: FramePayload): Record<string, string | number | null>[] {
  const firstValid: Record<string, number> = {};
  frame.columns.forEach((col, j) => {
    for (let i = 0; i < frame.index.length; i++) {
      const v = frame.data[i]?.[j];
      if (v !== null && v !== undefined && Number.isFinite(v) && v !== 0) {
        firstValid[col] = v;
        break;
      }
    }
  });
  return frame.index.map((date, i) => {
    const row: Record<string, string | number | null> = { date };
    frame.columns.forEach((col, j) => {
      const v = frame.data[i]?.[j];
      const base = firstValid[col];
      row[col] = v !== null && v !== undefined && base ? (v / base) * 100 : null;
    });
    return row;
  });
}

function drawdownRows(result: AnalysisResult): Record<string, string | number | null>[] {
  const dates = new Set<string>();
  Object.values(result.drawdowns).forEach((m) => Object.keys(m).forEach((d) => dates.add(d)));
  return [...dates].sort().map((date) => {
    const row: Record<string, string | number | null> = { date };
    Object.entries(result.drawdowns).forEach(([ticker, series]) => {
      row[ticker] = series[date] ?? null;
    });
    return row;
  });
}

function Tip({ active, payload, label, isPct }: { active?: boolean; payload?: { name: string; value: number }[]; label?: string; isPct?: boolean }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tip">
      <strong>{label}</strong>
      {payload.map((p) => (
        <div key={p.name}>
          {p.name}: {isPct ? pct(p.value) : Number(p.value).toLocaleString("pt-BR", { maximumFractionDigits: 4 })}
        </div>
      ))}
    </div>
  );
}

export function PriceChart({ prices }: { prices: FramePayload }) {
  const data = frameToSeries(prices);
  return (
    <div className="chart-card">
      <h3>Preços ajustados</h3>
      <p className="muted">Séries individuais; interrupções aparecem como lacunas (sem conexão artificial).</p>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid stroke="#e6ebf0" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip content={<Tip />} />
          <Legend />
          {prices.columns.map((c, i) => (
            <Line key={c} type="linear" dataKey={c} stroke={PALETTE[i % PALETTE.length]} dot={false} connectNulls={false} strokeWidth={1.8} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Base100Chart({ prices }: { prices: FramePayload }) {
  const data = pricesToBase100(prices);
  return (
    <div className="chart-card">
      <h3>Comparação normalizada (base 100)</h3>
      <p className="muted">Primeira cotação válida de cada série = 100. Sem conversão cambial.</p>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid stroke="#e6ebf0" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip content={<Tip />} />
          <Legend />
          {prices.columns.map((c, i) => (
            <Line key={c} type="linear" dataKey={c} stroke={PALETTE[i % PALETTE.length]} dot={false} connectNulls={false} strokeWidth={1.8} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DrawdownChart({ result }: { result: AnalysisResult }) {
  const data = drawdownRows(result);
  const cols = Object.keys(result.drawdowns);
  return (
    <div className="chart-card">
      <h3>Drawdown (amostra alinhada)</h3>
      <p className="muted">Trajetória de riqueza com base W₀ = 1 sobre retornos alinhados.</p>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid stroke="#e6ebf0" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
          <YAxis tickFormatter={(v) => pct(v, 0)} tick={{ fontSize: 11 }} />
          <Tooltip content={<Tip isPct />} />
          <Legend />
          {cols.map((c, i) => (
            <Line key={c} type="linear" dataKey={c} stroke={PALETTE[i % PALETTE.length]} dot={false} connectNulls={false} strokeWidth={1.8} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RiskReturnScatter({ metrics }: { metrics: Record<string, AssetMetrics> }) {
  const data = Object.values(metrics)
    .filter((m) => m.mean_daily != null && m.std_daily != null)
    .map((m) => ({
      ticker: m.ticker,
      vol: m.std_daily as number,
      mean: m.mean_daily as number,
    }));
  return (
    <div className="chart-card">
      <h3>Dispersão: volatilidade × média diária</h3>
      <p className="muted">Eixo X: desvio padrão amostral diário. Eixo Y: média diária (estimativa histórica).</p>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart>
          <CartesianGrid stroke="#e6ebf0" />
          <XAxis type="number" dataKey="vol" name="Volatilidade" tickFormatter={(v) => pct(v, 1)} tick={{ fontSize: 11 }} />
          <YAxis type="number" dataKey="mean" name="Média" tickFormatter={(v) => pct(v, 2)} tick={{ fontSize: 11 }} />
          <ZAxis range={[80, 80]} />
          <Tooltip
            formatter={(value: number, name: string) => [pct(value), name === "vol" ? "Volatilidade" : "Média"]}
            labelFormatter={() => ""}
          />
          <Scatter data={data} fill="#003366" name="Ativos" />
        </ScatterChart>
      </ResponsiveContainer>
      <ul className="scatter-legend">
        {data.map((d) => (
          <li key={d.ticker}>
            <strong>{d.ticker}</strong>: vol {pct(d.vol)} · média {pct(d.mean)}
          </li>
        ))}
      </ul>
    </div>
  );
}
