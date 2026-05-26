import React from "react";
import ReactDOM from "react-dom/client";
import { AlertTriangle, CalendarClock, DollarSign, TrendingUp } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

type Allocation = {
  symbol: string;
  name: string;
  base_weight: number;
  final_weight: number;
  dollars: number;
  tilt: number;
};

type Metric = {
  symbol: string;
  name: string;
  latest_date: string;
  latest_close: number;
  sma_50: number | null;
  sma_100: number | null;
  sma_200: number | null;
  distance_sma_50: number | null;
  distance_sma_100: number | null;
  distance_sma_200: number | null;
  return_1m: number | null;
  return_3m: number | null;
  return_6m: number | null;
  drawdown_52w: number | null;
  signal_score: number;
  signal_label: "overweight" | "neutral" | "underweight";
  reasons: string[];
};

type DashboardData = {
  generated_at: string;
  latest_market_date: string;
  status: { ok: boolean; warnings: string[] };
  config: {
    monthly_contribution: number;
    tilt_strength: number;
    max_monthly_shift: number;
  };
  metrics: Metric[];
  allocations: Allocation[];
  disclaimer: string;
};

const colors = ["#2563eb", "#059669", "#dc2626", "#7c3aed", "#d97706", "#0891b2"];

function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function metricBySymbol(metrics: Metric[], symbol: string): Metric {
  const metric = metrics.find((item) => item.symbol === symbol);
  if (!metric) throw new Error(`Missing metric for ${symbol}`);
  return metric;
}

function App() {
  const [data, setData] = React.useState<DashboardData | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/latest.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Failed to load dashboard data: ${response.status}`);
        return response.json() as Promise<DashboardData>;
      })
      .then(setData)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Unknown error"));
  }, []);

  if (error) {
    return (
      <main className="app-shell">
        <section className="state-panel">
          <AlertTriangle aria-hidden="true" />
          <h1>Econ Track</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="app-shell">
        <section className="state-panel">
          <h1>Econ Track</h1>
          <p>Loading latest allocation data...</p>
        </section>
      </main>
    );
  }

  const chartData = data.allocations.map((allocation) => ({
    symbol: allocation.symbol,
    dollars: allocation.dollars,
    weight: allocation.final_weight,
  }));

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Personal DCA dashboard</p>
          <h1>Econ Track</h1>
          <p className="subtitle">
            Rule-based monthly allocation signals for index funds and ETFs, generated from static market data.
          </p>
        </div>
        <div className={data.status.ok ? "status-pill ok" : "status-pill warning"}>
          {data.status.ok ? "Data current" : "Using last good data"}
        </div>
      </header>

      {data.status.warnings.length > 0 && (
        <section className="warning-strip">
          <AlertTriangle aria-hidden="true" />
          <span>{data.status.warnings[data.status.warnings.length - 1]}</span>
        </section>
      )}

      <section className="summary-grid">
        <SummaryCard icon={<DollarSign />} label="Monthly contribution" value={formatMoney(data.config.monthly_contribution)} />
        <SummaryCard icon={<CalendarClock />} label="Market date" value={data.latest_market_date} />
        <SummaryCard icon={<TrendingUp />} label="Tilt strength" value={formatPercent(data.config.tilt_strength)} />
      </section>

      <section className="dashboard-grid">
        <div className="panel allocation-panel">
          <div className="panel-heading">
            <h2>Monthly allocation</h2>
            <p>Auto allocation from base weights plus bounded trend tilts.</p>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="symbol" />
              <YAxis tickFormatter={(value) => `$${value}`} />
              <Tooltip formatter={(value) => formatMoney(Number(value))} />
              <Bar dataKey="dollars" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={entry.symbol} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel rules-panel">
          <div className="panel-heading">
            <h2>System settings</h2>
            <p>Configured for moderate monthly shifts.</p>
          </div>
          <dl>
            <div>
              <dt>Contribution</dt>
              <dd>{formatMoney(data.config.monthly_contribution)}</dd>
            </div>
            <div>
              <dt>Max monthly shift</dt>
              <dd>{formatPercent(data.config.max_monthly_shift)}</dd>
            </div>
            <div>
              <dt>Generated</dt>
              <dd>{new Date(data.generated_at).toLocaleString()}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Signals and allocations</h2>
          <p>Positive tilts combine trend strength, pullbacks, momentum, and drawdown context.</p>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Signal</th>
                <th>Allocation</th>
                <th>Dollars</th>
                <th>50D</th>
                <th>200D</th>
                <th>3M</th>
                <th>52W DD</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {data.allocations.map((allocation) => {
                const metric = metricBySymbol(data.metrics, allocation.symbol);
                return (
                  <tr key={allocation.symbol}>
                    <td>
                      <strong>{allocation.symbol}</strong>
                      <span>{allocation.name}</span>
                    </td>
                    <td>
                      <span className={`signal ${metric.signal_label}`}>{metric.signal_label}</span>
                    </td>
                    <td>{formatPercent(allocation.final_weight)}</td>
                    <td>{formatMoney(allocation.dollars)}</td>
                    <td>{formatPercent(metric.distance_sma_50)}</td>
                    <td>{formatPercent(metric.distance_sma_200)}</td>
                    <td>{formatPercent(metric.return_3m)}</td>
                    <td>{formatPercent(metric.drawdown_52w)}</td>
                    <td>{metric.reasons.join(", ")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <footer>
        <p>{data.disclaimer}</p>
      </footer>
    </main>
  );
}

function SummaryCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <section className="summary-card">
      <div className="summary-icon">{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </section>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
