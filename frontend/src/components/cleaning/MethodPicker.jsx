const NUMERIC_METHODS = [
  { value: "mean", label: "Fill with mean" },
  { value: "median", label: "Fill with median" },
  { value: "knn", label: "KNN imputation" },
  { value: "constant", label: "Fill with a constant" },
  { value: "drop_rows", label: "Drop rows with nulls" },
];

const CATEGORICAL_METHODS = [
  { value: "mode", label: "Fill with mode (most frequent)" },
  { value: "constant", label: "Fill with a constant / 'Unknown'" },
  { value: "drop_rows", label: "Drop rows with nulls" },
];

export default function MethodPicker({
  eda,
  column,
  method,
  value,
  onColumnChange,
  onMethodChange,
  onValueChange,
}) {
  const columnsWithMissing = eda.missing_values.filter(
    (m) => m.missing_count > 0
  );
  const numericColumns = new Set(eda.column_types.numeric);
  const isNumericColumn = column && numericColumns.has(column);
  const methodOptions = isNumericColumn ? NUMERIC_METHODS : CATEGORICAL_METHODS;

  return (
    <div className="flex flex-col gap-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-gray-600">
          Column
        </label>
        <select
          value={column || ""}
          onChange={(e) => onColumnChange(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="" disabled>
            Select a column with missing values…
          </option>
          {columnsWithMissing.map((m) => (
            <option key={m.column} value={m.column}>
              {m.column} ({m.missing_count} missing)
            </option>
          ))}
        </select>
      </div>

      {column && (
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Method
          </label>
          <select
            value={method || ""}
            onChange={(e) => onMethodChange(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="" disabled>
              Select a cleaning method…
            </option>
            {methodOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {method === "constant" && (
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            Constant value
          </label>
          <input
            type="text"
            value={value || ""}
            onChange={(e) => onValueChange(e.target.value)}
            placeholder={isNumericColumn ? "e.g. 0" : "e.g. Unknown"}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
      )}
    </div>
  );
}