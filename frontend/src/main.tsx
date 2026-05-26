import React from "react";
import ReactDOM from "react-dom/client";
import {
  AlertTriangle,
  CalendarClock,
  CircleHelp,
  DollarSign,
  Gauge,
  Moon,
  PiggyBank,
  Sun,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

type Strategy = "dip_uptrend" | "momentum" | "mean_reversion";

type Allocation = {
  symbol: string;
  name: string;
  strategy: Strategy;
  base_dollars: number;
  reserve_dollars: number;
  total_dollars: number;
  final_weight: number;
  opportunity_score: number;
};

type Metric = {
  symbol: string;
  name: string;
  latest_date: string;
  latest_close: number;
  sma_5: number | null;
  sma_10: number | null;
  sma_15: number | null;
  sma_50: number | null;
  sma_200: number | null;
  distance_sma_5: number | null;
  distance_sma_10: number | null;
  distance_sma_15: number | null;
  distance_sma_50: number | null;
  distance_sma_200: number | null;
  sma_5_change: number | null;
  sma_10_change: number | null;
  sma_15_change: number | null;
  return_3m: number | null;
  drawdown_52w: number | null;
  signal_score: number;
  signal_label: "overweight" | "neutral" | "underweight";
  reasons: string[];
};

type Volatility = {
  symbol: string;
  latest_date: string;
  latest_close: number;
  average_20d: number | null;
  regime: "calm" | "normal" | "elevated" | "stressed";
};

type DashboardData = {
  generated_at: string;
  latest_market_date: string;
  status: { ok: boolean; warnings: string[] };
  config: {
    contribution_per_asset: number;
    runs_per_month: string[];
    reserve_cash_per_run: number;
    default_strategy: Strategy;
    base_deployment_per_run: number;
    base_deployment_per_month: number;
  };
  volatility: Volatility;
  metrics: Metric[];
  strategy_allocations: Record<Strategy, Allocation[]>;
  allocations: Allocation[];
  disclaimer: string;
};

const strategyLabels: Record<Strategy, { label: string; description: string }> = {
  dip_uptrend: {
    label: "Dip within uptrend",
    description: "Adds reserve to funds pulling back while the 3-week trend still looks intact.",
  },
  momentum: {
    label: "Momentum",
    description: "Adds reserve to funds above short moving averages with improving MA slopes.",
  },
  mean_reversion: {
    label: "Mean reversion",
    description: "Adds reserve to the deepest short-term discounts, throttled by volatility.",
  },
};

const tooltipText: Record<string, string> = {
  signal: "Longer-horizon trend label from 50D/200D trend, 3M return, and 52-week drawdown.",
  allocation: "Share of this DCA run after base dollars plus any reserve deployment.",
  base: "Scheduled contribution that is always deployed to each configured fund.",
  reserve: "Extra cash suggested by the selected strategy. Base dollars are never reduced.",
  total: "Base dollars plus suggested reserve dollars for this DCA run.",
  ma1w: "Price distance from the 5 trading-day moving average.",
  ma2w: "Price distance from the 10 trading-day moving average.",
  ma3w: "Price distance from the 15 trading-day moving average.",
  maChange: "Average change across the 1W, 2W, and 3W moving averages.",
  score: "Strategy-specific opportunity score used to split reserve cash.",
  vix: "Cboe VIX regime. Elevated or stressed volatility throttles reserve deployment.",
  rationale: "Plain-English reasons from longer-horizon trend signals.",
};

const colors = {
  base: "#5b7c99",
  reserve: "#6f9f8c",
  amber: "#b88b4a",
  risk: "#b76767",
  neutral: "#7d8794",
  ink: "#17202e",
};

function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatNumber(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "n/a";
  return value.toFixed(2);
}

function metricBySymbol(metrics: Metric[], symbol: string): Metric {
  const metric = metrics.find((item) => item.symbol === symbol);
  if (!metric) throw new Error(`Missing metric for ${symbol}`);
  return metric;
}

function averageShortMaChange(metric: Metric): number | null {
  const values = [metric.sma_5_change, metric.sma_10_change, metric.sma_15_change].filter(
    (value): value is number => value !== null,
  );
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function nextDcaWindow(): string {
  const day = new Date().getDate();
  if (day <= 7) return "beginning of month";
  if (day <= 21) return "middle of month";
  return "next beginning";
}

function App() {
  const [data, setData] = React.useState<DashboardData | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [strategy, setStrategy] = React.useState<Strategy>("mean_reversion");
  const [theme, setTheme] = React.useState<"light" | "dark">(() => {
    const stored = window.localStorage.getItem("econ-track-theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  React.useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/latest.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Failed to load dashboard data: ${response.status}`);
        return response.json() as Promise<DashboardData>;
      })
      .then((payload) => {
        setData(payload);
        setStrategy(payload.config.default_strategy);
      })
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Unknown error"));
  }, []);

  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("econ-track-theme", theme);
  }, [theme]);

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

  const allocations = data.strategy_allocations[strategy] ?? data.allocations;
  const deployedThisRun = allocations.reduce((sum, allocation) => sum + allocation.total_dollars, 0);
  const reserveUsed = allocations.reduce((sum, allocation) => sum + allocation.reserve_dollars, 0);

  const chartData = allocations.map((allocation) => ({
    symbol: allocation.symbol,
    base: allocation.base_dollars,
    reserve: allocation.reserve_dollars,
    total: allocation.total_dollars,
  }));

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Bimonthly DCA dashboard</p>
          <h1>Econ Track</h1>
          <p className="subtitle">
            A static allocation cockpit for scheduled index-fund buys, short moving-average tilts, and volatility-aware reserve deployment.
          </p>
        </div>
        <div className="header-actions">
          <button
            className="theme-toggle"
            type="button"
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? <Moon aria-hidden="true" /> : <Sun aria-hidden="true" />}
            <span>{theme === "light" ? "Dark" : "Light"}</span>
          </button>
          <div className={data.status.ok ? "status-pill ok" : "status-pill warning"}>
            {data.status.ok ? "Data current" : "Using last good data"}
          </div>
        </div>
      </header>

      {data.status.warnings.length > 0 && (
        <section className="warning-strip">
          <AlertTriangle aria-hidden="true" />
          <span>{data.status.warnings[data.status.warnings.length - 1]}</span>
        </section>
      )}

      <section className="summary-grid">
        <SummaryCard icon={<DollarSign />} label="Base per run" value={formatMoney(data.config.base_deployment_per_run)} />
        <SummaryCard icon={<PiggyBank />} label="Reserve used" value={`${formatMoney(reserveUsed)} / ${formatMoney(data.config.reserve_cash_per_run)}`} />
        <SummaryCard icon={<Gauge />} label="VIX regime" value={`${data.volatility.regime} (${formatNumber(data.volatility.latest_close)})`} />
        <SummaryCard icon={<CalendarClock />} label="Next DCA window" value={nextDcaWindow()} />
      </section>

      <section className="control-band">
        <div>
          <h2>Strategy</h2>
          <p>{strategyLabels[strategy].description}</p>
        </div>
        <div className="segmented-control" role="tablist" aria-label="Allocation strategy">
          {(Object.keys(strategyLabels) as Strategy[]).map((key) => (
            <button
              key={key}
              className={strategy === key ? "active" : ""}
              type="button"
              role="tab"
              aria-selected={strategy === key}
              onClick={() => setStrategy(key)}
            >
              {strategyLabels[key].label}
            </button>
          ))}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel allocation-panel">
          <div className="panel-heading">
            <h2>Per-run deployment</h2>
            <p>
              {formatMoney(deployedThisRun)} suggested for the selected strategy, across {data.config.runs_per_month.length} monthly runs.
            </p>
          </div>
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="symbol" />
              <YAxis tickFormatter={(value) => `$${value}`} />
              <ChartTooltip formatter={(value) => formatMoney(Number(value))} />
              <Bar dataKey="base" stackId="cash" fill={colors.base} radius={[0, 0, 4, 4]} />
              <Bar dataKey="reserve" stackId="cash" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={entry.symbol} fill={index % 2 ? colors.reserve : "#7aa58f"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel rules-panel">
          <div className="panel-heading">
            <h2>Run settings</h2>
            <p>Base contribution is protected; only reserve cash changes.</p>
          </div>
          <dl>
            <div>
              <dt>Per fund, per run</dt>
              <dd>{formatMoney(data.config.contribution_per_asset)}</dd>
            </div>
            <div>
              <dt>Monthly base</dt>
              <dd>{formatMoney(data.config.base_deployment_per_month)}</dd>
            </div>
            <div>
              <dt>Market date</dt>
              <dd>{data.latest_market_date}</dd>
            </div>
            <div>
              <dt>
                VIX context <Info text={tooltipText.vix} />
              </dt>
              <dd>
                {formatNumber(data.volatility.latest_close)} vs 20D avg {formatNumber(data.volatility.average_20d)}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Signals and allocations</h2>
          <p>Short moving averages drive the reserve overlay; longer signals explain broader trend context.</p>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <Th label="Ticker" />
                <Th label="Signal" tip={tooltipText.signal} />
                <Th label="Allocation" tip={tooltipText.allocation} />
                <Th label="Base" tip={tooltipText.base} />
                <Th label="Reserve" tip={tooltipText.reserve} />
                <Th label="Total" tip={tooltipText.total} />
                <Th label="1W MA" tip={tooltipText.ma1w} />
                <Th label="2W MA" tip={tooltipText.ma2w} />
                <Th label="3W MA" tip={tooltipText.ma3w} />
                <Th label="MA Change" tip={tooltipText.maChange} />
                <Th label="Score" tip={tooltipText.score} />
                <Th label="Rationale" tip={tooltipText.rationale} />
              </tr>
            </thead>
            <tbody>
              {allocations.map((allocation) => {
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
                    <td>{formatMoney(allocation.base_dollars)}</td>
                    <td className={allocation.reserve_dollars > 0 ? "positive" : ""}>
                      {formatMoney(allocation.reserve_dollars)}
                    </td>
                    <td>{formatMoney(allocation.total_dollars)}</td>
                    <td>{formatPercent(metric.distance_sma_5)}</td>
                    <td>{formatPercent(metric.distance_sma_10)}</td>
                    <td>{formatPercent(metric.distance_sma_15)}</td>
                    <td>{formatPercent(averageShortMaChange(metric))}</td>
                    <td>{formatPercent(allocation.opportunity_score)}</td>
                    <td>{metric.reasons.join(", ")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="glossary-grid">
        {Object.entries({
          "1W / 2W / 3W MA": "Distances from 5, 10, and 15 trading-day moving averages. Negative means price is below that average.",
          "MA Change": "Average slope of the short moving averages. Falling averages can increase mean-reversion opportunity but also signal risk.",
          Reserve: "Optional extra cash deployed above the protected base contribution. VIX throttles this when volatility is elevated.",
          VIX: "Cboe's volatility index. Higher readings imply more expected S&P 500 volatility and reduce aggressive reserve deployment.",
        }).map(([term, definition]) => (
          <article className="glossary-item" key={term}>
            <h3>{term}</h3>
            <p>{definition}</p>
          </article>
        ))}
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

function Th({ label, tip }: { label: string; tip?: string }) {
  return (
    <th>
      <span className="th-label">
        {label}
        {tip && <Info text={tip} />}
      </span>
    </th>
  );
}

function Info({ text }: { text: string }) {
  return (
    <span className="info-tip" tabIndex={0} aria-label={text}>
      <CircleHelp aria-hidden="true" />
      <span className="tooltip" role="tooltip">
        {text}
      </span>
    </span>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
