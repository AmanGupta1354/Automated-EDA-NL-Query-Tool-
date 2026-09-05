export default function SheetPicker({ sheets, onSelect, loading }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-gray-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-gray-800">
        This workbook has multiple sheets
      </h2>
      <p className="mt-1 text-sm text-gray-500">
        Pick the one you want to work with. You can't switch sheets later
        without re-uploading.
      </p>
      <div className="mt-4 flex flex-col gap-2">
        {sheets.map((sheet) => (
          <button
            key={sheet}
            disabled={loading}
            onClick={() => onSelect(sheet)}
            className="rounded-lg border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700 hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-50"
          >
            {sheet}
          </button>
        ))}
      </div>
    </div>
  );
}