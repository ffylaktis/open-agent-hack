# Agent architecture

```mermaid
flowchart TB
  U(["User question"]) --> ORCH["Orchestrator<br/>loop ≤ MAX_ROUNDS, bounds, trace"]

  subgraph AGENT["AGENT — specialized roles (separate Nemotron calls)"]
    direction TB
    PL["Planner<br/>decompose → sub-questions + source"]
    AN["Analyst<br/>write Lightning SQL, rows → Evidence"]
    XS["cross_source<br/>trialed × cleared + indication mismatch"]
    RP["Reporter<br/>draft claims, each with evidence_ids"]
    EV["Evaluator<br/>isolated input: claim + cited evidence only<br/>verdict, default UNSUPPORTED"]
    PL --> AN --> XS --> RP --> EV
    EV -- "unsupported → bounce back" --> AN
    EV -- "all supported" --> FIN(["Cited answer<br/>rejected claims shown dropped"])
  end

  ORCH --> PL

  subgraph TOOLS["TOOLS — read-only guard, strip ';', LIMIT"]
    RS["run_sql · search_trials · search_devices"]
  end
  AN --> RS
  XS --> RS

  subgraph DATA["DATA — Zetaris (live per query)"]
    CT[("ctgov.trials<br/>ctgov.interventions")]
    FDA[("openfda.ai_devices")]
  end
  RS --> CT
  RS --> FDA

  subgraph MEM["SHARED MEMORY — H-MEM (Meterless Engine)"]
    EVID[("Evidence records<br/>source · provenance=SQL · confidence")]
  end
  AN --> EVID
  XS --> EVID
  RP -. reads .-> EVID
  EV -. reads .-> EVID

  subgraph POWER["POWER — model route"]
    MET["Meterless Nightshift :8088"] --> NEM["NVIDIA Nemotron<br/>+ signed receipt → DGX"]
  end
  PL -. call .-> MET
  AN -. call .-> MET
  RP -. call .-> MET
  EV -. call .-> MET

  TR[["trace.py — every step, verdict, receipt"]]
  ORCH -. logs .-> TR

  classDef data fill:#e8f4ea,stroke:#258A98;
  classDef power fill:#eef2ff,stroke:#5b6cc8;
  classDef mem fill:#fdf3e3,stroke:#C8902A;
  class CT,FDA data;
  class MET,NEM power;
  class EVID mem;
```

## Reading it
- **One request** flows Planner → Analyst → cross_source → Reporter → Evaluator, looping up to `MAX_ROUNDS`.
- **Feedback loop (the differentiator):** Evaluator bounces any unsupported claim back to the Analyst; only evidence-backed claims survive.
- **Every data fetch** is live Lightning SQL over Zetaris (`ctgov.*`, `openfda.*`) through read-only tools.
- **Evidence** lives in H-MEM (the required Meterless Engine) with mandatory `source`/`provenance`/`confidence`.
- **Every model call** routes through Meterless → Nemotron, returning a signed receipt (Sponsor-tech + DGX).
- **trace.py** records every step, verdict, and receipt (Technical + the demo's "show how it reasoned").
