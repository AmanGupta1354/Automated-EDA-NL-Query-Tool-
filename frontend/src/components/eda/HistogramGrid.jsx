import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function histogramToChartData(histogram) {
  if (!histogram) return [];
  const { bin_edges, counts } = histogram;
  return counts.map((count, i) => ({
    range: `${bin_edges[i].toFixed(1)}–${bin_edges[i + 1].toFixed(1)}`,
    count,
  }));
}

export default function HistogramGrid({ numericSummary }) {
  const withHistograms = numericSummary.filter((col) => col.histogram);

  if (withHistograms.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No numeric columns with data to chart.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      {withHistograms.map((col) => (
        <div
          key={col.column}
          className="rounded-lg border border-gray-200 bg-white p-4"
        >
          <h3 className="mb-2 text-sm font-semibold text-gray-700">
            {col.column}
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramToChartData(col.histogram)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="range"
                  tick={{ fontSize: 9 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1 text-xs text-gray-500">
            <span>mean: {col.mean?.toFixed(2) ?? "—"}</span>
            <span>median: {col.p50?.toFixed(2) ?? "—"}</span>
            <span>std: {col.std?.toFixed(2) ?? "—"}</span>
          </div>
        </div>
      ))}
    </div>
  );
}