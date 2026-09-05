export default function SummaryStatCards({ eda }) {
  const totalMissing = eda.missing_values.reduce(
    (sum, m) => sum + m.missing_count,
    0
  );

  const cards = [
    { label: "Rows", value: eda.shape.rows.toLocaleString() },
    { label: "Columns", value: eda.shape.columns },
    { label: "Duplicate rows", value: eda.duplicate_rows },
    { label: "Missing values", value: totalMissing.toLocaleString() },
    { label: "Memory", value: `${eda.memory_usage_mb} MB` },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-gray-200 bg-white p-4 text-center"
        >
          <div className="text-2xl font-semibold text-gray-900">
            {card.value}
          </div>
          <div className="mt-1 text-xs uppercase tracking-wide text-gray-500">
            {card.label}
          </div>
        </div>
      ))}
    </div>
  );
}