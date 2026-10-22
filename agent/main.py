"""The agent loop: Nemotron decides what to do, your code fetches the data it
asks for from Zetaris, the result goes back to Nemotron, and the loop repeats
until it can answer.

    User question -> model -> (tool call: run_sql) -> Zetaris -> model -> answer

Run:  python -m agent.main "your question"
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.llm import chat  # noqa: E402  (load_dotenv must run first)
from agent.tools_zetaris import run_sql, RUN_SQL_TOOL  # noqa: E402

SYSTEM = (
    "You are a data agent. Answer the user's question by querying the Zetaris "
    "data platform with the run_sql tool. Ground every answer in data you "
    "retrieved. Send one SQL statement per tool call."
)

MAX_STEPS = 6


def answer(question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for _ in range(MAX_STEPS):
        msg = chat(messages, tools=[RUN_SQL_TOOL])
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content or ""
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            try:
                rows = run_sql(args["sql"])
                content = json.dumps(rows)
            except Exception as error:  # feed the error back so the model can recover
                content = f"ERROR: {error}"
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": content}
            )
    return "Stopped: reached the step limit without a final answer."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "SELECT 1 — are you connected to Zetaris?"
    print(answer(q))
