"""Analyst agent — turns one sub-question into evidence by querying Zetaris via tools,
recovering from bad SQL, and writing results into H-MEM as Evidence records.
"""
import json
from agent import llm
from agent.tools_zetaris import DISPATCH, TOOLS, SqlError, ReadOnlyError
from agent.memory import Evidence
from agent.config import MAX_SQL_RETRIES

ANALYST_SYS = (
    "You are a data analyst. Answer the sub-question by calling a tool to query Zetaris, then stop. "
    "Tables: ctgov.trials(nct_id,title,status,phases,conditions,lead_sponsor,summary), "
    "ctgov.interventions(nct_id,intervention_type,intervention_name), "
    "openfda.ai_devices(k_number,device_name,applicant,decision_date,specialty). "
    "Prefer ONE read-only SQL statement (no trailing semicolon, qualified names), or a curated tool. "
    "Never write DDL/DML."
)

_ACCEPTS = {"run_sql": {"sql"}, "search_trials": {"condition", "device_only"}, "search_devices": {"term"}}


def _source_of(name, args):
    blob = (args.get("sql", "") + name).lower()
    return "openfda" if ("openfda" in blob or name == "search_devices") else "ctgov"


def _keywords(q):
    return [w for w in q.lower().replace(",", " ").replace("?", " ").split() if len(w) > 3][:8]


def analyze(subq, store, trace):
    """subq = {question, source}. Returns [Evidence] (also written to `store`)."""
    messages = [{"role": "system", "content": ANALYST_SYS},
                {"role": "user", "content": f"Sub-question ({subq.get('source','any')}): {subq['question']}"}]
    evidence = []
    for attempt in range(MAX_SQL_RETRIES + 1):
        msg, meta = llm.chat(messages, tools=TOOLS, think=False)
        trace.add("analyst", "model", {"attempt": attempt, "tool_calls": bool(msg.tool_calls)}, meta)
        if not msg.tool_calls:
            trace.add("analyst", "no_tool", {"content": (msg.content or "")[:200]})
            break
        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                           for tc in msg.tool_calls],
        })
        got = False
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}
            args = {k: v for k, v in args.items() if k in _ACCEPTS.get(name, set())}
            try:
                rows = DISPATCH[name](**args)
                trace.add("analyst", "tool_result", {"tool": name, "args": args, "n": len(rows)})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": json.dumps(rows[:30], default=str)})
                if rows:
                    ev = store.write(Evidence(
                        content=(f"Q: {subq['question']} | {name}({args}) -> {len(rows)} rows; "
                                 f"sample={json.dumps(rows[:3], default=str)[:400]}"),
                        source=_source_of(name, args),
                        provenance={"tool": name, "args": args, "sql": args.get("sql")},
                        tags=_keywords(subq["question"]), entities=_keywords(subq["question"]), rows=rows))
                    evidence.append(ev)
                    got = True
            except (SqlError, ReadOnlyError) as e:
                trace.add("analyst", "tool_error", {"tool": name, "error": str(e)[:200]})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": f"ERROR: {e}. Fix the statement and retry."})
        if got:
            break
    return evidence
