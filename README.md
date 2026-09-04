# Automated EDA + NL-Query Tool for Tabular Datasets

A single-session web app for exploring tabular data. Upload a CSV or Excel file, get an instant automated statistical profile, clean missing data on your own terms, and query the dataset in plain English through an LLM-powered agent.

> **Note:** This is a portfolio/demo project, not a production system. The NL-Query agent executes LLM-generated Python code against your data — see [Security Notes](#security-notes) below.

---

## Features

- **Automated EDA** — instant statistical profile on upload: column type detection, summary stats, missing-value breakdown, correlation matrix, histograms, and top categorical values.
- **Guided Data Cleaning** — user-directed, per-column cleaning (mean, median, KNN, mode, constant fill, or row drop). Nothing is cleaned automatically — every action requires explicit confirmation.
- **NL-Query** — ask questions about your data in plain English (e.g. *"average fare by class"*). An LLM agent translates the question into pandas code, runs it, and returns the answer. This is **not** semantic search — no embeddings or vector similarity are involved.
- **Multi-sheet Excel support** — pick which sheet to work with before anything else happens.
- **Full reset** — one-click "Start Over" restores the dataset to its original, untouched state.
- **Export** — download your cleaned dataset in the same format you uploaded it in (CSV → CSV, XLSX → XLSX).

---

## Tech Stack

| Layer      | Technology                                      |
|------------|--------------------------------------------------|
| Frontend   | React (JavaScript), Tailwind CSS, Recharts / Chart.js |
| Backend    | FastAPI (Python), Uvicorn                        |
| Data       | Pandas                                           |
| AI Agent   | LangChain (`create_pandas_dataframe_agent`)      |
| File Types | CSV, Excel (`.xlsx`), including multi-sheet files |

---

## How It Works

1. **Upload** a CSV or XLSX file.
2. If the XLSX file has multiple sheets, you're prompted to **pick one** before anything else happens.
3. The backend loads the file and returns an **automated EDA report** on the raw data.
4. Review the EDA report, including a missing-value breakdown per column.
5. To clean missing data:
   - Pick a column and a cleaning method.
   - Confirm the exact effect (e.g. *"This will fill 42 missing values in 'Age' with the median — proceed?"*).
   - Only on confirmation does the backend mutate the working data. This is irreversible on its own step — there's no per-step undo.
   - The EDA report refreshes automatically to reflect the change.
6. Repeat cleaning for as many columns as needed.
7. Hit **Start Over** at any time to discard all cleaning and reset to the original upload. This is the only rollback mechanism.
8. Use the **NL-Query chat** to ask questions — it always runs against the *current* (possibly cleaned) working data.
9. Hit **Finish** to export the current working data as a downloadable file, in the same format you uploaded.

---

## Session Model

Each upload creates an in-memory session (no persistent storage, no multi-dataset library):

- `original_df` — untouched snapshot from upload/sheet-selection, kept for full reset
- `working_df` — the DataFrame that cleaning actions mutate, and that EDA/NL-Query operate on
- `filename`, `file_format` (`csv` / `xlsx`), `active_sheet` (if applicable)

Only one active dataset is supported per session at a time.

---

## API Endpoints

| Method | Endpoint                          | Description |
|--------|------------------------------------|--------------|
| `POST` | `/upload`                          | Upload a CSV/XLSX file; returns `dataset_id`, sheet list (if XLSX), and raw EDA (if no sheet selection is needed) |
| `POST` | `/select-sheet/{dataset_id}`       | (XLSX only) Set active sheet, initialize session, return EDA |
| `GET`  | `/eda/{dataset_id}`                | Return EDA report reflecting current working data |
| `POST` | `/clean/apply/{dataset_id}`        | Apply a confirmed cleaning action; returns updated EDA |
| `POST` | `/reset/{dataset_id}`              | Restore working data from the original snapshot |
| `POST` | `/query/{dataset_id}`              | Run an NL-Query question against the current working data |
| `GET`  | `/export/{dataset_id}`             | Download the current working data in the original upload format |
| `DELETE` | `/dataset/{dataset_id}`          | Clear the session from memory |

Full request/response schemas are documented in [`docs/api-schemas.md`](docs/api-schemas.md) *(or inline in the project spec)*.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An API key from an LLM provider (OpenAI, Anthropic, etc.) for the NL-Query agent

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
OPENAI_API_KEY=your_key_here
# or ANTHROPIC_API_KEY=your_key_here, depending on provider
```

---

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI app & routes
│   ├── eda.py                # EDA profiling module
│   ├── cleaning.py           # Guided cleaning logic
│   ├── nl_query.py           # LangChain pandas agent
│   └── session.py            # In-memory session/dataset store
├── frontend/
│   ├── src/
│   │   ├── components/       # Upload, EDA dashboard, cleaning panel, chat, etc.
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## Constraints & Design Decisions

- **No multi-dataset library** — single active dataset per session, in-memory only, no persistence.
- **No upload size/row cap** — this is demo scale.
- **No step-by-step undo** — only a full reset to the original snapshot.
- **Cleaning is never automatic** — every mutation requires an explicit user action + confirmation.
- **Naming convention** — the plain-English query feature is called **NL-Query** everywhere (code, UI, docs). It is intentionally never referred to as "semantic search," since it does not use embeddings or vector similarity.

---

## Security Notes

The NL-Query feature executes LLM-generated Python code against your dataframe via LangChain's `create_pandas_dataframe_agent`. This is a real code-execution surface. It's acceptable for a portfolio/demo project, but if you plan to expose this beyond local/personal use, add sandboxing, timeouts, and resource limits before treating it as production-hardened.

---

## Roadmap

- [ ] Backend EDA module
- [ ] Session & cleaning logic
- [ ] NL-Query agent integration
- [ ] React frontend
- [ ] Deployment guide

---

## License

MIT (or your preferred license)
