"""Structured trace — every agent step/verdict/receipt/tokens (Technical + the demo's
'show how it reasoned')."""
import json
import time


class Trace:
    def __init__(self):
        self.events = []
        self._step = 0

    def add(self, agent, action, payload=None, meta=None):
        self._step += 1
        ev = {"t": round(time.time(), 3), "step": self._step, "agent": agent, "action": action, "payload": payload}
        if meta:
            ev["route"] = meta.get("route")
            ev["receipt_id"] = meta.get("receipt_id")
            ev["routed_model"] = meta.get("routed_model")
            usage = meta.get("usage") or {}
            ev["tokens"] = usage.get("total_tokens")
            if meta.get("fallback_reason"):
                ev["fallback_reason"] = meta["fallback_reason"]
        self.events.append(ev)
        return ev

    def dump(self, path=None):
        s = json.dumps(self.events, indent=2, default=str)
        if path:
            open(path, "w", encoding="utf-8").write(s)
        return s

    def summary(self):
        out = []
        for e in self.events:
            tag = f"  [{e['route']}]" if e.get("route") else ""
            if e.get("fallback_reason"):
                tag += f" (fallback: {e['fallback_reason']})"
            out.append(f"{e['step']:>2}. {e['agent']}.{e['action']}{tag}")
        return out
