"""
nl_query_agent.py — NL-Query: natural language to pandas Q&A via LangChain.

NAMING NOTE: this feature is called "NL-Query" everywhere. It is NOT
semantic search: no embeddings, no vector similarity. The agent
translates a plain-English question into pandas code, executes it
against the CURRENT working_df, and returns text/numbers.

Design notes:
- Pure function over (df, question) — no session/FastAPI awareness.
- KNOWN CAVEAT: this agent executes LLM-generated Python. Real
  code-execution surface — fine for a demo, not production-hardened
  without sandboxing/timeouts.
- KNOWN CAVEAT: langchain-experimental (owner of
  create_pandas_dataframe_agent) is in sunset/deprecated status upstream.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import pandas as pd

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

DEFAULT_MODEL = os.environ.get("NL_QUERY_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.0
MAX_ITERATIONS = 10
MAX_EXECUTION_SECONDS = 30

SYSTEM_PREFIX = """You are a data analysis assistant. You have access to a
pandas DataFrame called `df` that has already been loaded for you.

STRICT RULES — follow all of these without exception:
1. Answer ONLY using the data in `df`. Do not use outside/world knowledge,
   even if you happen to know something related to the topic.
2. NEVER invent, assume, or hallucinate column names or values that are
   not actually present in `df`. If a column the user seems to be asking
   about doesn't exist, say so explicitly instead of guessing.
3. If the question cannot be answered from `df` as it currently exists,
   say so clearly rather than fabricating a plausible-sounding answer.
4. Do all analysis by writing and executing pandas code against `df`.
   Do not answer from memory or general reasoning alone.
5. Keep your final answer concise and directly responsive to the question.
"""


class NLQueryError(Exception):
    """Maps to the API doc's 500 agent_execution_failed error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class QueryAnswer:
    answer: str
    generated_code: str | None
    result_type: str  # "text" | "number" | "table"


def _build_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    return ChatOpenAI(model=model, temperature=temperature)


def _build_agent(df: pd.DataFrame, llm):
    """Fresh agent per request — df changes after every cleaning action
    and reset, so caching an agent against a stale df is unsafe."""
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type="tool-calling",
        prefix=SYSTEM_PREFIX,
        verbose=False,
        return_intermediate_steps=True,
        max_iterations=MAX_ITERATIONS,
        max_execution_time=MAX_EXECUTION_SECONDS,
        allow_dangerous_code=True,
        include_df_in_prompt=True,
        number_of_head_rows=5,
    )


def _extract_generated_code(intermediate_steps: list) -> str | None:
    """Pull the pandas code the agent actually ran, from the LAST tool
    call (the one whose result produced the final answer)."""
    if not intermediate_steps:
        return None

    last_action, _observation = intermediate_steps[-1]
    tool_input = getattr(last_action, "tool_input", None)

    if isinstance(tool_input, dict):
        for key in ("query", "__arg1", "code"):
            if key in tool_input:
                return str(tool_input[key])
        if len(tool_input) == 1:
            return str(next(iter(tool_input.values())))
        return str(tool_input)

    if tool_input is not None:
        return str(tool_input)

    return None


_NUMBER_RE = re.compile(r"^\s*-?\d+(\.\d+)?\s*%?\s*$")


def _classify_result_type(answer_text: str) -> str:
    """Heuristic classification into text/number/table for frontend
    rendering decisions."""
    stripped = answer_text.strip()

    if _NUMBER_RE.match(stripped):
        return "number"

    line_count = stripped.count("\n") + 1
    if line_count >= 2 and re.search(r"\S {2,}\S", stripped):
        return "table"

    return "text"


def answer_question(
    df: pd.DataFrame,
    question: str,
    llm=None,
) -> QueryAnswer:
    """Run the NL-Query agent against the given DataFrame — should
    always be the session's current working_df, never original_df."""
    if not question or not question.strip():
        raise NLQueryError("Question cannot be empty.")

    llm = llm or _build_llm()
    agent = _build_agent(df, llm)

    try:
        result = agent.invoke({"input": question})
    except Exception as exc:
        raise NLQueryError(
            "Could not resolve a valid pandas operation for this question. "
            "Try rephrasing."
        ) from exc

    answer_text = result.get("output", "")
    intermediate_steps = result.get("intermediate_steps", [])

    if not answer_text or not answer_text.strip():
        raise NLQueryError(
            "The agent did not produce an answer. Try rephrasing the question."
        )

    generated_code = _extract_generated_code(intermediate_steps)
    result_type = _classify_result_type(answer_text)

    return QueryAnswer(
        answer=answer_text.strip(),
        generated_code=generated_code,
        result_type=result_type,
    )