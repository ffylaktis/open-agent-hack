"""Cross-source join (the innovation) — reconcile what's TRIALED (ctgov) against what's
CLEARED (openfda) for a condition, and surface the indication gap. Deterministic retrieval;
the Reporter/Evaluator do the reasoning on top of these grounded building blocks.
"""
from agent.tools_zetaris import search_trials, search_devices, _trials_sql, _devices_sql
from agent.memory import Evidence

_MODALITY_TERMS = ["transcranial", "deep brain", "vagus", "neurostim"]


def _mk(content, source, sql, rows, tags):
    return Evidence(content=content, source=source,
                    provenance={"tool": "cross_source", "sql": sql},
                    rows=rows, confidence=(0.95 if rows else 0.9), tags=tags, entities=tags)


def cross_source(condition, store, trace):
    """Returns [Evidence]: trialed device modalities, cleared devices per modality, indication check."""
    ev = []
    # A — device interventions TRIALED for the condition (ctgov)
    trials = search_trials(condition, device_only=True, limit=100)
    names = sorted({(r.get("intervention_name") or "") for r in trials if r.get("intervention_name")})
    ev.append(store.write(_mk(
        f"Device interventions TRIALED for '{condition}': {len(trials)} trial-arms; examples={names[:8]}",
        "ctgov", _trials_sql(condition, True, 100), trials, [condition, "trialed", "device"])))
    trace.add("cross_source", "trialed", {"n": len(trials), "modalities": names[:8]})

    # B — FDA-CLEARED neuro devices matching the trialed modalities (openfda)
    blob = " ".join(names).lower()
    terms = {t for t in _MODALITY_TERMS if t.split()[0] in blob} or {"transcranial"}
    for t in sorted(terms):
        rows = search_devices(t, limit=50)
        ev.append(store.write(_mk(
            f"FDA-CLEARED neuro devices matching modality '{t}': {len(rows)}; "
            f"examples={[r.get('device_name') for r in rows[:5]]}",
            "openfda", _devices_sql(t), rows, [condition, "cleared", t])))
        trace.add("cross_source", "cleared", {"term": t, "n": len(rows)})

    # C — indication check: does ANY cleared neuro device reference the condition?
    cind = search_devices(condition, limit=50)
    ev.append(store.write(_mk(
        (f"INDICATION CHECK: no FDA-cleared neuro device record references '{condition}' "
         f"(indication inferred from device name/panel; {len(cind)} matches)."
         if not cind else f"{len(cind)} cleared neuro devices reference '{condition}'."),
        "openfda", _devices_sql(condition), cind, [condition, "indication", "cleared"])))
    trace.add("cross_source", "indication_check", {"n": len(cind)})
    return ev
