import { useState } from "react";
import MethodPicker from "./MethodPicker";
import ConfirmationModal from "./ConfirmationModal";
import StartOverButton from "./StartOverButton";

export default function CleaningPanel({ eda, onClean, onStartOver, loading }) {
  const [column, setColumn] = useState("");
  const [method, setMethod] = useState("");
  const [value, setValue] = useState("");
  const [confirming, setConfirming] = useState(false);

  const missingCount =
    eda.missing_values.find((m) => m.column === column)?.missing_count ?? 0;

  const canSubmit =
    column && method && (method !== "constant" || value.trim() !== "");

  const handleColumnChange = (col) => {
    setColumn(col);
    setMethod("");
    setValue("");
  };

  const handleConfirm = async () => {
    try {
      await onClean(column, method, method === "constant" ? value : null);
      setConfirming(false);
      setColumn("");
      setMethod("");
      setValue("");
    } catch {
      // error is surfaced via the global error banner — just close the
      // modal so the user can retry.
      setConfirming(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Clean missing data
        </h2>
        <StartOverButton onConfirm={onStartOver} disabled={loading} />
      </div>

      <MethodPicker
        eda={eda}
        column={column}
        method={method}
        value={value}
        onColumnChange={handleColumnChange}
        onMethodChange={setMethod}
        onValueChange={setValue}
      />

      <button
        onClick={() => setConfirming(true)}
        disabled={!canSubmit || loading}
        className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
      >
        Apply cleaning
      </button>

      {confirming && (
        <ConfirmationModal
          column={column}
          method={method}
          value={value}
          missingCount={missingCount}
          onConfirm={handleConfirm}
          onCancel={() => setConfirming(false)}
          loading={loading}
        />
      )}
    </div>
  );
}