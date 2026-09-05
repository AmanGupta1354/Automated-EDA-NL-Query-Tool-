import CleaningPanel from "./components/cleaning/CleaningPanel";
import EdaDashboard from "./components/eda/EdaDashboard";
import NlQueryChat from "./components/query/NlQueryChat";
import ErrorBanner from "./components/shared/ErrorBanner";
import ExportButton from "./components/shared/ExportButton";
import SheetPicker from "./components/upload/SheetPicker";
import UploadDropzone from "./components/upload/UploadDropzone";
import { useDatasetSession } from "./hooks/useDatasetSession";

export default function App() {
  const session = useDatasetSession();

  const hasDataset = Boolean(session.datasetId);
  const showSheetPicker = hasDataset && session.needsSheetSelection;
  const showDashboard = hasDataset && !session.needsSheetSelection && session.eda;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              EDA + NL-Query Tool
            </h1>
            {session.filename && (
              <p className="text-xs text-gray-500">{session.filename}</p>
            )}
          </div>
          {hasDataset && (
            <div className="flex items-center gap-3">
              {showDashboard && (
                <ExportButton
                  onExport={session.exportCurrent}
                  fileFormat={session.fileFormat}
                />
              )}
              <button
                onClick={session.startNewSession}
                className="text-sm font-medium text-gray-500 hover:text-gray-800"
              >
                New dataset
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8">
        <ErrorBanner message={session.error} onDismiss={session.clearError} />

        {!hasDataset && (
          <UploadDropzone
            onFileSelected={session.upload}
            loading={session.loading}
          />
        )}

        {showSheetPicker && (
          <SheetPicker
            sheets={session.sheets}
            onSelect={session.pickSheet}
            loading={session.loading}
          />
        )}

        {showDashboard && (
          <>
            <EdaDashboard eda={session.eda} />
            <CleaningPanel
              eda={session.eda}
              onClean={session.clean}
              onStartOver={session.startOver}
              loading={session.loading}
            />
            <NlQueryChat onQuery={session.query} />
          </>
        )}
      </main>
    </div>
  );
}