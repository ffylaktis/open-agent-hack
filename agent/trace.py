"""Structured trace — every agent step/verdict/receipt (Technical + the demo's 'show how it reasoned')."""
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
        self.events.append(ev)
        return ev

    def dump(self, path=None):
        s = json.dumps(self.events, indent=2, default=str)
        if path:
            open(path, "w", encoding="utf-8").write(s)
        return s

    def summary(self):
        return [f"{e['step']:>2}. {e['agent']}.{e['action']}" + (f"  [{e['route']}]" if e.get("route") else "")
                for e in self.events]
