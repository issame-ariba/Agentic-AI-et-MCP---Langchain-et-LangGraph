from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


def create_chat_model() -> ChatGroq:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and configure it."
        )
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
        api_key=api_key,
    )
