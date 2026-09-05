"""
nl_query_agent.py — NL-Query: natural language to pandas Q&A via LangChain.

NAMING NOTE: this feature is called "NL-Query" everywhere — in code,
UI copy, and docs. It is NOT semantic search: there are no embeddings
and no vector similarity involved. The agent translates a plain-English
question into pandas code, executes that code against the CURRENT
working_df, and returns the result as text/numbers.

Single entry point: answer_question(df, question, llm=None) -> dict
matching the POST /query/{dataset_id} response shape (minus dataset_id
and the echoed question, which the route layer adds).

Design notes:
- Pure function over (df, question) — no session/FastAPI awareness.
- KNOWN CAVEAT: this agent executes LLM-generated Python via
  LangChain's python_repl_ast tool — a real code-execution surface.
  Fine for a demo, not production-hardened without sandboxing/timeouts.
- KNOWN CAVEAT: langchain-experimental (owner of
  create_pandas_dataframe_agent) is in sunset/deprecated status upstream.
- KNOWN CAVEAT: running fully locally via Ollama trades cost for
  quality — small local models are noticeably worse than GPT-4o-mini
  at reliably writing correct pandas code, especially for multi-step
  or ambiguous questions. Expect more "agent gave up" / wrong-answer
  cases than a hosted-API setup would produce.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import pandas as pd

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# ---- config ---------------------------------------------------------------

DEFAULT_MODEL = os.environ.get("NL_QUERY_MODEL", "gemini-2.0-flash")
DEFAULT_TEMPERATURE = 0.0
MAX_ITERATIONS = 10
MAX_EXECUTION_SECONDS = 30

# Strict system prefix: keeps the agent scoped to the dataset it was
# given, and explicitly forbids it from filling gaps with outside
# knowledge or inventing columns/values that don't exist in the df.
SYSTEM_PREFIX = """You are a data analysis assistant. You have access to a
pandas DataFrame called `df` that has already been loaded for you.

STRICT RULES — follow all of these without exception:
1. Answer ONLY using the data in `df`. Do not use outside/world knowledge,
   even if you happen to know something related to the topic.
2. NEVER invent, assume, or hallucinate column names or values that are
   not actually present in `df`. If a column the user seems to be asking
   about doesn't exist, say so explicitly instead of guessing.
3. If the question cannot be answered from `df` as it currently exists
   (e.g. missing column, ambiguous request, insufficient data), say so
   clearly rather than fabricating a plausible-sounding answer.
4. Do all analysis by writing and executing pandas code against `df`.
   Do not answer from memory or general reasoning alone.
5. Keep your final answer concise and directly responsive to the question
   — state the result, not a narrative of how you got there.
"""


class NLQueryError(Exception):
    """Raised when the agent fails to produce a usable answer — bad
    question, agent gave up after max iterations, execution error inside
    the generated pandas code, etc. Maps to the API doc's 500
    agent_execution_failed error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class QueryAnswer:
    answer: str
    generated_code: str | None
    result_type: str  # "text" | "number" | "table"


def _build_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    return ChatGoogleGenerativeAI(model=model, temperature=temperature)


def _build_agent(df: pd.DataFrame, llm):
    """Construct a fresh agent bound to the given DataFrame.

    A new agent is built per-request rather than cached, since df
    changes after every cleaning action and after reset — caching an
    agent against a stale df would silently answer questions about data
    that no longer reflects the current working_df.
    """
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type="tool-calling",
        prefix=SYSTEM_PREFIX,
        verbose=False,
        return_intermediate_steps=True,
        max_iterations=MAX_ITERATIONS,
        max_execution_time=MAX_EXECUTION_SECONDS,
        allow_dangerous_code=True,  # see module docstring's code-execution caveat
        include_df_in_prompt=True,
        number_of_head_rows=5,
    )


def _extract_generated_code(intermediate_steps: list) -> str | None:
    """Pull the pandas code the agent actually ran out of the
    intermediate_steps returned by AgentExecutor.

    Each step is (AgentAction, observation). The python_repl_ast tool's
    input is the code string, though depending on agent_type it may
    arrive as a plain string or as a dict like {"query": "..."}. We take
    the LAST tool call as the "generated_code" shown to the user, since
    that's the one whose result produced the final answer.
    """
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
    """Best-effort classification of the final answer text into
    text/number/table, so the frontend can decide whether to render a
    stat card, a small table, or plain prose."""
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
    always be the session's current working_df, never original_df.

    Raises NLQueryError if the agent fails to produce an answer for any
    reason. The route layer should catch that and return a 500 with
    {error: "agent_execution_failed", message: exc.message}.
    """
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