"""Minimal local web UI for the Evidence-Intelligence Agent — zero extra dependencies
(Python stdlib http.server). Serves one self-contained page + a /ask endpoint over
orchestrator.run(). Defaults to instant SAMPLE_MODE replay; a 'Run live' toggle runs fresh.

    python -m agent.web      ->  http://127.0.0.1:7000
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from dotenv import load_dotenv
load_dotenv()

from agent.orchestrator import run, _load_sample              # noqa: E402
from agent.config import SAMPLE_PATH                           # noqa: E402
from agent.tools_zetaris import ReadOnlyError, SqlError, run_sql  # noqa: E402

DEMO_Q = ("What neuromodulation is being trialed for anorexia nervosa, "
          "and is any of it FDA-cleared for that use?")
STRESS = ["rTMS is FDA-cleared to treat anorexia nervosa."]


def _serialize(res):
    ev = [{"id": r.get("id"), "source": r.get("source"), "content": r.get("content", ""),
           "sql": (r.get("provenance") or {}).get("sql", "")} for r in res.get("evidence", [])]
    tr = res.get("trace")
    return {
        "question": res.get("question"), "condition": res.get("condition"),
        "replayed": bool(res.get("replayed")),
        "supported": [{"claim": v["claim"], "evidence_ids": v.get("evidence_ids", [])} for v in res.get("supported", [])],
        "dropped": [{"claim": v["claim"], "reason": v.get("reason", "")} for v in res.get("dropped", [])],
        "evidence": ev,
        "telemetry": res.get("telemetry", {}),
        "trace": tr.summary() if hasattr(tr, "summary") else (tr or []),
    }


# Page content is rendered entirely with safe DOM methods (textContent / createElement) on the
# client — no innerHTML with dynamic data, so model/data output can't inject markup.
HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence-Intelligence Agent</title>
<style>
 :root{--ink:#14202b;--muted:#5b6b7a;--line:#e3e9ef;--bg:#f6f8fa;--card:#fff;
   --teal:#128a98;--teal-bg:#e8f6f7;--gold:#b8842a;--red:#c0392b;}
 *{box-sizing:border-box} body{margin:0;background:var(--bg)}
 .wrap{font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);min-height:100vh;line-height:1.5}
 header{background:var(--card);border-bottom:1px solid var(--line);padding:22px 26px}
 h1{margin:0;font-size:20px;letter-spacing:-.01em}
 .sub{color:var(--muted);font-size:13px;margin-top:4px;max-width:70ch}
 .sponsors{font-family:ui-monospace,monospace;font-size:11px;color:var(--muted);margin-top:8px}
 main{max-width:960px;margin:0 auto;padding:24px 20px 60px}
 .ask{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
 textarea{width:100%;border:1px solid var(--line);border-radius:8px;padding:12px;font:inherit;resize:vertical;min-height:62px}
 .btns{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap;align-items:center}
 button{font:inherit;font-weight:600;border:0;border-radius:8px;padding:10px 16px;cursor:pointer}
 .primary{background:var(--teal);color:#fff} .ghost{background:#eef2f5;color:var(--ink)}
 button:disabled{opacity:.5;cursor:default}
 .status{color:var(--muted);font-size:13px}
 .meta{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0 6px;align-items:center}
 .chip{font-family:ui-monospace,monospace;font-size:11px;background:#eef2f5;border:1px solid var(--line);border-radius:999px;padding:3px 9px;color:var(--muted)}
 .badge{background:var(--gold);color:#fff;border:0}
 .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-top:14px}
 .card h2{margin:0 0 10px;font-size:12.5px;text-transform:uppercase;letter-spacing:.06em}
 .ok{border-left:3px solid var(--teal)} .ok h2{color:var(--teal)}
 .bad{border-left:3px solid var(--red)} .bad h2{color:var(--red)}
 .claim{padding:10px 0;border-top:1px solid var(--line)} .claim:first-of-type{border-top:0}
 .claim .t{font-size:14px} .reason{color:var(--muted);font-size:12.5px;margin-top:5px}
 .cites{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}
 .cite{font-family:ui-monospace,monospace;font-size:10.5px;background:var(--teal-bg);color:var(--teal);border-radius:6px;padding:2px 7px;cursor:help}
 details{margin-top:14px} summary{cursor:pointer;font-size:13px;color:var(--muted);font-weight:600;padding:6px 0}
 .ev{font-size:12.5px;padding:8px 0;border-top:1px solid var(--line)} .ev:first-child{border-top:0}
 .ev .s{font-family:ui-monospace,monospace;font-size:10.5px;color:var(--teal);margin-right:6px}
 .trace div{font-family:ui-monospace,monospace;font-size:11.5px;color:var(--muted);line-height:1.7}
 .empty{color:var(--muted);font-size:13px}
</style></head><body><div class="wrap">
 <header>
   <h1>Evidence-Intelligence Agent</h1>
   <div class="sub">Answers clinical-evidence questions and <b>shows its receipts</b> — every claim is traced to the
     query behind it, and the Evaluator deletes any claim it can't back. · Open Agent Hackathon · Track 02</div>
   <div class="sponsors">Zetaris (governed SQL) · Meterless H-MEM + Nightshift (signed receipts) · NVIDIA Nemotron</div>
 </header>
 <main>
   <div class="ask">
     <textarea id="q"></textarea>
     <div class="btns">
       <button class="primary" id="replay">&#9889; Instant replay</button>
       <button class="ghost" id="runlive">&#9654; Run live (2-3 min)</button>
       <span class="status" id="status"></span>
     </div>
   </div>
   <div id="out"></div>
 </main></div>
<script>
const DEMO=%DEMO%;
const $=id=>document.getElementById(id);
$("q").value=DEMO;
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n;}
function errorCard(msg){const c=el("div","card bad");c.appendChild(el("h2",null,"Error"));c.appendChild(el("div","reason",msg));return c;}
async function ask(live){
  $("status").textContent = live ? "Running the agent live: plan \\u2192 gather \\u2192 report \\u2192 evaluate..." : "Replaying the recorded run...";
  $("replay").disabled=$("runlive").disabled=true; $("out").replaceChildren();
  try{
    const r=await fetch("/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:$("q").value,live:live})});
    const d=await r.json();
    if(d.error){$("out").replaceChildren(errorCard(d.error));} else render(d);
  }catch(e){$("out").replaceChildren(errorCard(e.message));}
  finally{$("status").textContent="";$("replay").disabled=$("runlive").disabled=false;}
}
function render(d){
  const out=$("out"); out.replaceChildren();
  const ev={}; (d.evidence||[]).forEach(e=>ev[e.id]=e);
  const t=d.telemetry||{};
  const meta=el("div","meta");
  meta.appendChild(el("span","chip badge", d.replayed?"recorded demo":"live"));
  ["condition: "+(d.condition||""), "route: meterless x"+((t.routes&&t.routes.meterless)||0),
   "tokens: "+(t.total_tokens||0), "receipts: "+((t.receipts||[]).length)].forEach(x=>meta.appendChild(el("span","chip",x)));
  out.appendChild(meta);

  const ok=el("div","card ok"); ok.appendChild(el("h2",null,"\\u2705 Answer - evidence-backed"));
  if((d.supported||[]).length){ d.supported.forEach(c=>{
    const cl=el("div","claim"); cl.appendChild(el("div","t",c.claim));
    const cites=el("div","cites");
    (c.evidence_ids||[]).forEach(id=>{const e=ev[id]; const chip=el("span","cite", e?e.source:id); chip.setAttribute("title", e?(e.sql||e.content):""); cites.appendChild(chip);});
    cl.appendChild(cites); ok.appendChild(cl);
  }); } else ok.appendChild(el("div","empty","No claim passed verification."));
  out.appendChild(ok);

  const bad=el("div","card bad"); bad.appendChild(el("h2",null,"\\u2717 Rejected by the Evaluator"));
  if((d.dropped||[]).length){ d.dropped.forEach(c=>{const cl=el("div","claim"); cl.appendChild(el("div","t","\\u2717 "+c.claim)); cl.appendChild(el("div","reason",c.reason)); bad.appendChild(cl);}); }
  else bad.appendChild(el("div","empty","Nothing rejected."));
  out.appendChild(bad);

  const d1=el("details"); d1.appendChild(el("summary",null,"Evidence ("+((d.evidence||[]).length)+")"));
  const ec=el("div","card"); (d.evidence||[]).forEach(e=>{const row=el("div","ev"); row.appendChild(el("span","s",e.source)); row.appendChild(document.createTextNode((e.content||"").slice(0,240))); ec.appendChild(row);});
  d1.appendChild(ec); out.appendChild(d1);

  const d2=el("details"); d2.appendChild(el("summary",null,"Trace ("+((d.trace||[]).length)+" steps)"));
  const tc=el("div","card trace"); (d.trace||[]).forEach(l=>tc.appendChild(el("div",null,l)));
  d2.appendChild(tc); out.appendChild(d2);
}
$("replay").onclick=()=>ask(false); $("runlive").onclick=()=>ask(true);
</script></body></html>"""
HTML = HTML.replace("%DEMO%", json.dumps(DEMO_Q))


def healthz():
    """Dependency snapshot for ops/demo. Never raises; a down dep is JSON 'down', not a 500."""
    zetaris, reason = "ok", None
    try:
        run_sql("SELECT 1")
    except (SqlError, ReadOnlyError, Exception) as e:
        zetaris, reason = "down", str(e)[:200]

    base = os.environ.get("METERLESS_BASE_URL")
    if not base:
        meterless = "unset"
    else:
        try:
            token = os.environ.get("METERLESS_RUNTIME_TOKEN", "")
            r = requests.get(
                base.rstrip("/") + "/models",
                headers={"Authorization": "Bearer " + token},
                timeout=3,
            )
            meterless = "ok" if r.status_code < 500 else "down"
        except Exception:
            meterless = "down"

    sample = "present" if os.path.exists(SAMPLE_PATH) else "missing"
    body = {
        "zetaris": zetaris,
        "meterless": meterless,
        "sample": sample,
        "status": "ok" if zetaris == "ok" else "degraded",
    }
    if reason:
        body["reason"] = reason
    return body


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        elif self.path == "/healthz":
            try:
                self._send(200, json.dumps(healthz()))
            except Exception as e:                       # never 500 — ops still gets a body
                self._send(200, json.dumps({
                    "zetaris": "down", "meterless": "down", "sample": "missing",
                    "status": "degraded", "reason": str(e)[:200],
                }))
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            q = (body.get("question") or DEMO_Q).strip()
            live = bool(body.get("live"))
            if not live and os.path.exists(SAMPLE_PATH):
                res = _load_sample()
            else:
                res = run(q, stress_claims=STRESS, allow_sample=False)   # "Run live" always runs live
            self._send(200, json.dumps(_serialize(res)))
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)[:300]}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("UI_PORT", "7000"))
    print(f"Evidence-Intelligence Agent UI  ->  http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
