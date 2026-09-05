"""
routers/query.py — POST /query/{dataset_id}

Runs the NL-Query agent against the session's CURRENT working_df.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.nl_query_agent import answer_question
from app.models import QueryRequest, QueryResponse
from app.session_store import session_store

router = APIRouter(tags=["query"])


@router.post("/query/{dataset_id}", response_model=QueryResponse)
async def query_dataset(dataset_id: str, body: QueryRequest) -> QueryResponse:
    session = session_store.get_ready_session(dataset_id)

    result = answer_question(session.working_df, body.question)

    return QueryResponse(
        dataset_id=dataset_id,
        question=body.question,
        answer=result.answer,
        generated_code=result.generated_code,
        result_type=result.result_type,
    )