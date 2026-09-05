import { useCallback, useRef, useState } from "react";

const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];

function isAcceptedFile(file) {
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export default function UploadDropzone({ onFileSelected, loading }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState(null);
  const inputRef = useRef(null);

  const handleFile = useCallback(
    (file) => {
      if (!file) return;
      if (!isAcceptedFile(file)) {
        setLocalError("Only .csv and .xlsx files are supported.");
        return;
      }
      setLocalError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files?.[0];
      handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="mx-auto max-w-xl">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          isDragOver
            ? "border-indigo-500 bg-indigo-50"
            : "border-gray-300 bg-gray-50 hover:border-gray-400"
        }`}
      >
        <p className="text-lg font-medium text-gray-700">
          {loading ? "Uploading…" : "Drop your CSV or XLSX file here"}
        </p>
        <p className="mt-1 text-sm text-gray-500">or click to browse</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      {localError && (
        <p className="mt-2 text-sm text-red-600">{localError}</p>
      )}
    </div>
  );
}