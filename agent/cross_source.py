"""Cross-source join (the innovation) — reconcile what's TRIALED (ctgov) against what's
CLEARED (openfda) for a condition, and surface the indication gap. Deterministic retrieval;
the Reporter/Evaluator reason on top of these grounded building blocks.

Epistemic note: openFDA 510(k) records carry NO indication-for-use field, so the indication
check can only BOUND absence (no record names the condition), never prove it. Claims are
scoped accordingly.
"""
from agent.tools_zetaris import search_trials, search_devices, _trials_sql, _devices_sql
from agent.memory import Evidence

# trialed-intervention-name token  ->  openfda.neuro_devices search term
_MODALITY_MAP = {
    "transcranial": "transcranial", "magnetic": "transcranial", "tdcs": "transcranial",
    "direct current": "transcranial", "theta": "transcranial", "rtms": "transcranial",
    "deep brain": "deep brain", "vagus": "vagus", "nerve stim": "vagus", "neurostim": "neurostim",
}


def _mk(content, source, sql, rows, tags):
    return Evidence(content=content, source=source,
                    provenance={"tool": "cross_source", "sql": sql},
                    rows=rows, confidence=(0.95 if rows else 0.9), tags=tags, entities=tags)


def cross_source(condition, store, trace):
    """Returns [Evidence]: trialed device modalities, cleared devices per modality, scoped indication check."""
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
    terms = {v for k, v in _MODALITY_MAP.items() if k in blob} or {"transcranial"}
    cleared_all = []
    for t in sorted(terms):
        rows = search_devices(t, limit=50)
        cleared_all += rows
        ev.append(store.write(_mk(
            f"FDA-CLEARED neuro devices matching modality '{t}': {len(rows)}; "
            f"examples={[r.get('device_name') for r in rows[:5]]}",
            "openfda", _devices_sql(t), rows, [condition, "cleared", t])))
        trace.add("cross_source", "cleared", {"term": t, "n": len(rows)})

    # C — scoped indication check: does ANY cleared record name the condition?
    specialties = sorted({(r.get("specialty") or "") for r in cleared_all if r.get("specialty")})
    cind = search_devices(condition, limit=50)
    if cind:
        content = f"{len(cind)} cleared neuro device records reference '{condition}'."
    else:
        content = (f"INDICATION CHECK (scoped): among the {len(cleared_all)} cleared neuro-device records searched, "
                   f"NONE name '{condition}'. 510(k) records carry no indication-for-use field; these devices fall "
                   f"under specialties {specialties[:4]}. This BOUNDS (does not prove) absence of a cleared "
                   f"'{condition}' indication.")
    ev.append(store.write(_mk(content, "openfda", _devices_sql(condition), cind, [condition, "indication", "cleared"])))
    trace.add("cross_source", "indication_check", {"n": len(cind), "specialties": specialties[:4]})
    return ev
