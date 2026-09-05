/**
 * api/client.js — Thin fetch wrappers over the FastAPI backend.
 *
 * Every function returns the parsed JSON body on success and THROWS an
 * ApiError (carrying { error, message } from the backend's shared error
 * shape) on any non-2xx response.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function handleResponse(response) {
  if (response.ok) {
    return response.json();
  }

  let code = "unknown_error";
  let message = `Request failed with status ${response.status}`;
  try {
    const body = await response.json();
    code = body.error || code;
    message = body.message || message;
  } catch {
    // response body wasn't JSON — fall back to the generic message above
  }
  throw new ApiError(response.status, code, message);
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

export async function selectSheet(datasetId, sheetName) {
  const response = await fetch(`${BASE_URL}/select-sheet/${datasetId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sheet_name: sheetName }),
  });
  return handleResponse(response);
}

export async function getEda(datasetId) {
  const response = await fetch(`${BASE_URL}/eda/${datasetId}`);
  return handleResponse(response);
}

export async function applyCleaning(datasetId, column, method, value) {
  const response = await fetch(`${BASE_URL}/clean/apply/${datasetId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column, method, value: value ?? null }),
  });
  return handleResponse(response);
}

export async function resetDataset(datasetId) {
  const response = await fetch(`${BASE_URL}/reset/${datasetId}`, {
    method: "POST",
  });
  return handleResponse(response);
}

export async function queryDataset(datasetId, question) {
  const response = await fetch(`${BASE_URL}/query/${datasetId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse(response);
}

export async function exportDataset(datasetId) {
  const response = await fetch(`${BASE_URL}/export/${datasetId}`);
  if (!response.ok) {
    return handleResponse(response); // will throw with the parsed error
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "export";
  return { blob, filename };
}

export async function deleteDataset(datasetId) {
  const response = await fetch(`${BASE_URL}/dataset/${datasetId}`, {
    method: "DELETE",
  });
  return handleResponse(response);
}