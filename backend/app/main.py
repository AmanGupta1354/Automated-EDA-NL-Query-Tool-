"""
main.py — FastAPI app entrypoint.

Run with: uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGINS
from app.exceptions import EXCEPTION_HANDLERS
from app.routers import cleaning, eda, export, query, session, upload

app = FastAPI(
    title="EDA + NL-Query Tool",
    description=(
        "Automated EDA and NL-Query (natural-language pandas Q&A via an "
        "LLM agent) for a single in-memory tabular dataset per session."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for exc_type, handler in EXCEPTION_HANDLERS:
    app.add_exception_handler(exc_type, handler)

app.include_router(upload.router)
app.include_router(eda.router)
app.include_router(cleaning.router)
app.include_router(query.router)
app.include_router(export.router)
app.include_router(session.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}