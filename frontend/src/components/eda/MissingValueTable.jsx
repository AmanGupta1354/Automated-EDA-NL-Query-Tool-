export default function MissingValueTable({ missingValues }) {
  const withMissing = missingValues.filter((m) => m.missing_count > 0);

  if (withMissing.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No missing values in the current dataset.
      </p>
    );
  }

  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
          <th className="py-2">Column</th>
          <th className="py-2">Missing count</th>
          <th className="py-2">Missing %</th>
        </tr>
      </thead>
      <tbody>
        {withMissing.map((m) => (
          <tr key={m.column} className="border-b border-gray-100">
            <td className="py-2 font-medium text-gray-800">{m.column}</td>
            <td className="py-2 text-gray-600">{m.missing_count}</td>
            <td className="py-2 text-gray-600">{m.missing_pct}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}