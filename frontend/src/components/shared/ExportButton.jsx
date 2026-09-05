export default function ExportButton({ onExport, fileFormat }) {
  return (
    <button
      onClick={onExport}
      className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
    >
      Finish — Export {fileFormat ? fileFormat.toUpperCase() : "file"}
    </button>
  );
}