"""Power layer: the Nemotron client.

Reads MODEL_BASE_URL, MODEL_API_KEY and NEMOTRON_MODEL from .env. For the
hackathon these point either at Meterless Nightshift (Route A) or NVIDIA's
free API (Route B) — always use all three from the SAME route.
"""
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("MODEL_BASE_URL"),
    api_key=os.environ.get("MODEL_API_KEY"),
)

MODEL = os.environ.get("NEMOTRON_MODEL")


def chat(messages: list, tools: list | None = None):
    """One turn with the model. Returns the raw message (may contain tool calls)."""
    kwargs = {"model": MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return client.chat.completions.create(**kwargs).choices[0].message
