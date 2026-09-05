function colorForCorrelation(value) {
  if (value === null || value === undefined) return "#f3f4f6"; // undefined correlation
  const clamped = Math.max(-1, Math.min(1, value));
  if (clamped >= 0) {
    const intensity = Math.round(clamped * 200);
    return `rgb(${255 - intensity}, ${255 - intensity}, 255)`;
  }
  const intensity = Math.round(-clamped * 200);
  return `rgb(255, ${255 - intensity}, ${255 - intensity})`;
}

export default function CorrelationHeatmap({ correlationMatrix }) {
  const { columns, matrix } = correlationMatrix;

  if (!columns || columns.length < 2) {
    return (
      <p className="text-sm text-gray-500">
        Need at least two numeric columns to compute correlations.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-1"></th>
            {columns.map((col) => (
              <th key={col} className="p-1 font-medium text-gray-600">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={columns[i]}>
              <td className="p-1 pr-2 text-right font-medium text-gray-600">
                {columns[i]}
              </td>
              {row.map((value, j) => (
                <td
                  key={j}
                  title={value === null ? "undefined" : value.toFixed(3)}
                  style={{ backgroundColor: colorForCorrelation(value) }}
                  className="h-10 w-10 text-center align-middle"
                >
                  {value === null ? "—" : value.toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}