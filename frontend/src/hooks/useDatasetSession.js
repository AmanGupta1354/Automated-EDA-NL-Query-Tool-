/**
 * hooks/useDatasetSession.js — Single source of truth for frontend state.
 *
 * Every mutating action (select sheet, clean, reset) updates `eda`
 * directly from that action's own response rather than issuing a
 * separate GET /eda call — the backend already returns the fresh
 * report on every mutation.
 */

import { useCallback, useState } from "react";
import {
  applyCleaning,
  deleteDataset,
  exportDataset,
  queryDataset,
  resetDataset,
  selectSheet,
  uploadDataset,
} from "../api/client";

export function useDatasetSession() {
  const [datasetId, setDatasetId] = useState(null);
  const [filename, setFilename] = useState(null);
  const [fileFormat, setFileFormat] = useState(null);
  const [sheets, setSheets] = useState(null);
  const [needsSheetSelection, setNeedsSheetSelection] = useState(false);
  const [eda, setEda] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const resetLocalState = useCallback(() => {
    setDatasetId(null);
    setFilename(null);
    setFileFormat(null);
    setSheets(null);
    setNeedsSheetSelection(false);
    setEda(null);
    setError(null);
  }, []);

  const upload = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    try {
      const body = await uploadDataset(file);
      setDatasetId(body.dataset_id);
      setFilename(body.filename);
      setFileFormat(body.file_format);
      setNeedsSheetSelection(body.needs_sheet_selection);
      setSheets(body.sheets);
      setEda(body.eda); // null while needs_sheet_selection is true
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const pickSheet = useCallback(
    async (sheetName) => {
      if (!datasetId) return;
      setLoading(true);
      setError(null);
      try {
        const body = await selectSheet(datasetId, sheetName);
        setNeedsSheetSelection(false);
        setEda(body.eda);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [datasetId]
  );

  const clean = useCallback(
    async (column, method, value) => {
      if (!datasetId) return;
      setLoading(true);
      setError(null);
      try {
        const body = await applyCleaning(datasetId, column, method, value);
        setEda(body.eda);
        return body.applied;
      } catch (err) {
        setError(err.message);
        throw err; // let the caller (ConfirmationModal) know it failed
      } finally {
        setLoading(false);
      }
    },
    [datasetId]
  );

  const startOver = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const body = await resetDataset(datasetId);
      setEda(body.eda);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const query = useCallback(
    async (question) => {
      if (!datasetId) throw new Error("No active dataset.");
      // Query errors are handled by the chat panel itself (shown inline
      // as a failed message bubble), not the global error banner.
      return queryDataset(datasetId, question);
    },
    [datasetId]
  );

  const exportCurrent = useCallback(async () => {
    if (!datasetId) return;
    setError(null);
    try {
      const { blob, filename: exportFilename } = await exportDataset(datasetId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = exportFilename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  }, [datasetId]);

  const startNewSession = useCallback(async () => {
    if (datasetId) {
      try {
        await deleteDataset(datasetId);
      } catch {
        // best-effort cleanup — if the session was already gone, that's fine
      }
    }
    resetLocalState();
  }, [datasetId, resetLocalState]);

  return {
    datasetId,
    filename,
    fileFormat,
    sheets,
    needsSheetSelection,
    eda,
    loading,
    error,
    upload,
    pickSheet,
    clean,
    startOver,
    query,
    exportCurrent,
    startNewSession,
    clearError: () => setError(null),
  };
}