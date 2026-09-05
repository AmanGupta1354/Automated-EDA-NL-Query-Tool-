import CorrelationHeatmap from "./CorrelationHeatmap";
import HistogramGrid from "./HistogramGrid";
import MissingValueTable from "./MissingValueTable";
import SummaryStatCards from "./SummaryStatCards";

function CategoricalSummary({ categoricalSummary }) {
  if (categoricalSummary.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {categoricalSummary.map((col) => {
        const maxCount = Math.max(...col.top_values.map((v) => v.count), 1);
        return (
          <div
            key={col.column}
            className="rounded-lg border border-gray-200 bg-white p-4"
          >
            <h3 className="mb-2 text-sm font-semibold text-gray-700">
              {col.column}{" "}
              <span className="font-normal text-gray-400">
                ({col.unique_count} unique)
              </span>
            </h3>
            <div className="flex flex-col gap-1.5">
              {col.top_values.map((v) => (
                <div key={v.value} className="flex items-center gap-2 text-xs">
                  <span className="w-20 shrink-0 truncate text-gray-600">
                    {v.value}
                  </span>
                  <div className="h-3 flex-1 rounded bg-gray-100">
                    <div
                      className="h-3 rounded bg-indigo-400"
                      style={{ width: `${(v.count / maxCount) * 100}%` }}
                    />
                  </div>
                  <span className="w-10 text-right text-gray-500">
                    {v.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function EdaDashboard({ eda }) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Dataset overview
        </h2>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            eda.is_cleaned
              ? "bg-emerald-100 text-emerald-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {eda.is_cleaned ? "Cleaned" : "Raw"}
        </span>
      </div>

      <SummaryStatCards eda={eda} />

      <section>
        <h3 className="mb-3 text-sm font-semibold text-gray-700">
          Missing values
        </h3>
        <MissingValueTable missingValues={eda.missing_values} />
      </section>

      {eda.numeric_summary.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-gray-700">
            Numeric distributions
          </h3>
          <HistogramGrid numericSummary={eda.numeric_summary} />
        </section>
      )}

      {eda.categorical_summary.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-gray-700">
            Categorical breakdown
          </h3>
          <CategoricalSummary categoricalSummary={eda.categorical_summary} />
        </section>
      )}

      {eda.correlation_matrix.columns.length >= 2 && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-gray-700">
            Correlation matrix
          </h3>
          <CorrelationHeatmap correlationMatrix={eda.correlation_matrix} />
        </section>
      )}
    </div>
  );
}