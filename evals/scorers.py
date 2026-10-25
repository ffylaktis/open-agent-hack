"""Structural / behavioral scorers over an orchestrator result dict.

Deliberately NOT LLM-judged: the Evaluator is the system under test, so grading it with the same
mechanism would be circular. These encode the invariants a *grounded* answer must satisfy; each
returns (passed: bool, detail: str)."""

_SCOPE_TOKENS = ("search", "dataset", "database", "record", "among", "in this",
                 "openfda", "ctgov", "clinicaltrials")
_NEG_TOKENS = ("no ", " not ", "none", "0 match", "zero", "returned no", "without")


def _supported(res):
    return res.get("supported") or []


def _dropped(res):
    return res.get("dropped") or []


def _evidence(res):
    return res.get("evidence") or []


def _telemetry(res):
    return res.get("telemetry") or {}


def answer_nonempty(res):
    a = (res.get("answer") or "").strip()
    return bool(a), f"answer length={len(a)}"


def cross_source_present(res):
    srcs = {e.get("source") for e in _evidence(res)}
    return ("ctgov" in srcs and "openfda" in srcs), f"sources={sorted(s for s in srcs if s)}"


def all_supported_cited(res):
    bad = [v["claim"][:60] for v in _supported(res) if not v.get("evidence_ids")]
    return (not bad), (f"{len(bad)} supported claim(s) uncited" if bad
                       else "every supported claim cites evidence")


def citations_resolve(res):
    ids = {e.get("id") for e in _evidence(res)}
    dangling = [i for v in _supported(res) for i in v.get("evidence_ids", []) if i not in ids]
    return (not dangling), (f"dangling citation ids: {dangling[:3]}" if dangling
                            else "every citation resolves to evidence")


def negatives_scoped(res):
    offenders = []
    for v in _supported(res):
        t = (v.get("claim") or "").lower()
        if any(k in t for k in _NEG_TOKENS) and not any(s in t for s in _SCOPE_TOKENS):
            offenders.append(v["claim"][:70])
    return (not offenders), (f"unscoped universal negative(s): {offenders}" if offenders
                             else "negative claims scoped to what was searched")


def ran_on_meterless(res):
    routes = _telemetry(res).get("routes") or {}
    return ("meterless" in routes), f"routes={routes}"


def receipts_present(res):
    n = len(_telemetry(res).get("receipts") or [])
    return (n > 0), f"{n} Meterless receipt(s) captured"


def overclaim_rejected(res, needle):
    needle = (needle or "").lower()
    in_dropped = any(needle in (d.get("claim") or "").lower() for d in _dropped(res))
    in_supported = any(needle in (v.get("claim") or "").lower() for v in _supported(res))
    return (in_dropped and not in_supported), (
        "overclaim correctly rejected" if in_dropped and not in_supported
        else "overclaim not in rejected set (or leaked into supported)")


SCORERS = {
    "answer_nonempty": answer_nonempty,
    "cross_source_present": cross_source_present,
    "all_supported_cited": all_supported_cited,
    "citations_resolve": citations_resolve,
    "negatives_scoped": negatives_scoped,
    "ran_on_meterless": ran_on_meterless,
    "receipts_present": receipts_present,
}
