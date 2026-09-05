"""
config.py — App-wide settings read from environment variables.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
NL_QUERY_MODEL = os.environ.get("NL_QUERY_MODEL", "gpt-4o-mini")