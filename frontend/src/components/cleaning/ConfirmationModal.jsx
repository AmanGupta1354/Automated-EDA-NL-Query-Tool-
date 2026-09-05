function describeEffect({ column, method, value, missingCount }) {
  if (method === "drop_rows") {
    return `This will remove ${missingCount} row${
      missingCount === 1 ? "" : "s"
    } where '${column}' is missing.`;
  }
  if (method === "constant") {
    return `This will fill ${missingCount} missing value${
      missingCount === 1 ? "" : "s"
    } in '${column}' with '${value}'.`;
  }
  if (method === "knn") {
    return `This will fill ${missingCount} missing value${
      missingCount === 1 ? "" : "s"
    } in '${column}' using KNN imputation based on other numeric columns.`;
  }
  return `This will fill ${missingCount} missing value${
    missingCount === 1 ? "" : "s"
  } in '${column}' with the column's ${method}.`;
}

export default function ConfirmationModal({
  column,
  method,
  value,
  missingCount,
  onConfirm,
  onCancel,
  loading,
}) {
  if (!column || !method) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-base font-semibold text-gray-900">
          Confirm cleaning action
        </h3>
        <p className="mt-2 text-sm text-gray-600">
          {describeEffect({ column, method, value, missingCount })}
        </p>
        <p className="mt-2 text-xs text-red-600">
          This action is irreversible on its own — the only way back is
          "Start Over," which resets ALL cleaning, not just this step.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={loading}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Applying…" : "Confirm"}
          </button>
        </div>
      </div>
    </div>
  );
}