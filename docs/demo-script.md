# Demo video script — Evidence-Intelligence Agent (Track 02)

**Target runtime:** ~95–105 s (limit 1–4 min, §6.1). **Format:** screen recording of the web UI in
deterministic replay + voiceover.

## Pre-flight
- Set `SAMPLE_MODE=1` in `.env` so the run **replays instantly** — no 3-min live wait, no flakiness on camera.
- Start the UI: `python -m agent.web` → open `http://127.0.0.1:7000`. The demo question is pre-filled.
- Record at 1080p. Tools: **OBS Studio** (capture) → **Descript** or **CapCut** (trim + auto-captions).
  Judges often watch muted — burn in captions.

## Shot-by-shot  (narration NeuroOptimized — 74/100; see note)

| Time | On screen | Narration |
|---|---|---|
| 0:00–0:12 | UI header | "Picture a clinician reading an AI answer with three confident citations — and two of them don't exist. That's not hypothetical: studies find up to 90% of AI medical citations are fabricated. This agent is built so that can't happen — it answers, and shows its receipts." |
| 0:12–0:24 | Question in box → click **⚡ Instant replay** | "Watch. I ask: what neuromodulation is being *trialed* for anorexia nervosa — and is any of it actually *FDA-cleared* for that use?" |
| 0:24–0:46 | Answer panel renders; hover a citation chip → SQL tooltip | "The answer appears, grounded in real data — tDCS, theta-burst, deep-brain stimulation — and every claim carries a clickable chip: hover, and the exact SQL query behind it appears. No citation, no claim." |
| 0:46–1:08 | The red **Rejected by the Evaluator** panel | "Then the part that matters turns red. A separate Evaluator re-checks each claim against only its own evidence and deletes what it can't back. It strikes out 'rTMS is FDA-cleared for anorexia' — the devices are cleared, but not one record mentions anorexia. The agent is telling you, out loud, *why* it refuses to say it." |
| 1:08–1:22 | Telemetry row (meterless ×N · tokens · receipts) | "Underneath: live Zetaris SQL across ClinicalTrials.gov and openFDA, reasoned by NVIDIA Nemotron through Meterless — every call stamped with a signed receipt, the whole run auditable." |
| 1:22–1:32 | Answer + rejected panels together | "An agent that works across sources, grounds every claim, and refuses to hallucinate. In clinical evidence, that's the difference between a tool you can trust and one you can't." |

**NeuroOptimizer:** the narration scores **74/100** overall (attention 78 · memory 82 · reward 75 · language 73 · emotional 71 · sensory 64) — up from 59 on the first draft. Five of six dimensions clear the 70 bar; *sensory richness* (64) is left by design, since more vivid imagery reads as marketing to a technical/clinical judging panel. Scored via the `neuro-optimizer` CLI per project rule.

## If you prefer a live run
Toggle **▶ Run live** (2–3 min; needs Zetaris + Meterless up). The recorded replay is recommended for the
video: identical output, deterministic, fast.
