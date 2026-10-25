"""Analyst agent — turns one sub-question into evidence by querying Zetaris via tools.
Runs a bounded tool loop (multiple queries allowed), recovers from bad SQL by feeding
the error back, and writes results into H-MEM as self-describing Evidence (dict rows).
"""
import json
from agent import llm
from agent.tools_zetaris import DISPATCH, TOOLS, SqlError, ReadOnlyError
from agent.memory import Evidence
from agent.config import MAX_STEPS

ANALYST_SYS = (
    "You are a data analyst. Answer the sub-question by calling tools to query Zetaris, then stop. "
    "Tables: ctgov.trials(nct_id,title,status,phases,conditions,lead_sponsor,summary), "
    "ctgov.interventions(nct_id,intervention_type,intervention_name), "
    "openfda.neuro_devices(k_number,device_name,applicant,decision_date,specialty)  -- cleared TMS/neuromod, "
    "openfda.ai_devices(k_number,device_name,applicant,decision_date,specialty). "
    "Use ONE read-only SQL statement per call (no trailing semicolon, qualified names) or a curated tool. "
    "Never write DDL/DML. When you have the data, reply with a one-line summary and no further tool calls."
)

_ACCEPTS = {"run_sql": {"sql"}, "search_trials": {"condition", "device_only"}, "search_devices": {"term"}}


def _source_of(name, args):
    blob = (str(args.get("sql", "")) + name).lower()
    return "openfda" if ("openfda" in blob or name == "search_devices") else "ctgov"


def _keywords(q):
    return [w for w in q.lower().replace(",", " ").replace("?", " ").split() if len(w) > 3][:8]


def analyze(subq, store, trace):
    """subq = {question, source}. Returns [Evidence] (also written to `store`)."""
    messages = [{"role": "system", "content": ANALYST_SYS},
                {"role": "user", "content": f"Sub-question ({subq.get('source', 'any')}): {subq['question']}"}]
    evidence = []
    for step in range(MAX_STEPS):
        msg, meta = llm.chat(messages, tools=TOOLS, think=False)
        trace.add("analyst", "model", {"step": step, "tool_calls": bool(msg.tool_calls)}, meta)
        if not msg.tool_calls:
            trace.add("analyst", "done", {"content": (msg.content or "")[:200]})
            break
        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                           for tc in msg.tool_calls],
        })
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}
            args = {k: v for k, v in args.items() if k in _ACCEPTS.get(name, set())}
            fn = DISPATCH.get(name)
            if fn is None:                                   # hallucinated tool name — don't crash
                trace.add("analyst", "tool_error", {"tool": name, "error": "unknown tool"})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": f"ERROR: unknown tool '{name}'."})
                continue
            try:
                rows = fn(**args)
                trace.add("analyst", "tool_result", {"tool": name, "args": args, "n": len(rows)})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": json.dumps(rows[:10], default=str)})  # cap context fed back
                if rows:
                    ev = store.write(Evidence(
                        content=(f"Q: {subq['question']} | {name}({args}) -> {len(rows)} rows; "
                                 f"sample={json.dumps(rows[:3], default=str)[:500]}"),
                        source=_source_of(name, args),
                        provenance={"tool": name, "args": args, "sql": args.get("sql")},
                        tags=_keywords(subq["question"]), entities=_keywords(subq["question"]),
                        rows=rows))
                    evidence.append(ev)
            except (SqlError, ReadOnlyError) as e:
                trace.add("analyst", "tool_error", {"tool": name, "error": str(e)[:200]})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": f"ERROR: {e}. Fix the statement and retry."})
    return evidence
