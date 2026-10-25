"""Model provider: Meterless Nightshift (primary, pinned Nemotron) with direct-NVIDIA fallback.

chat() returns (message, meta) where meta = {route, receipt_id, model}. The Meterless
receipt (routed_model/cost) is captured best-effort for the Sponsor-tech story + DGX prize.
"""
import os
from openai import OpenAI
from agent.config import PINNED_MODEL

_MET_BASE = os.environ.get("METERLESS_BASE_URL")
_MET_KEY = os.environ.get("METERLESS_RUNTIME_TOKEN")
_NV_BASE = os.environ.get("MODEL_BASE_URL")
_NV_KEY = os.environ.get("MODEL_API_KEY")
_NV_MODEL = os.environ.get("NEMOTRON_MODEL")

_meterless = (OpenAI(base_url=_MET_BASE, api_key=_MET_KEY, timeout=120,
                     default_headers={"meterless-app": "openagent-hack", "meterless-scope": "user"})
              if _MET_BASE and _MET_KEY else None)
_nvidia = OpenAI(base_url=_NV_BASE, api_key=_NV_KEY, timeout=120) if _NV_BASE and _NV_KEY else None


def _receipt(comp):
    try:
        return (comp.model_dump().get("meterless") or {}).get("receipt_id")
    except Exception:
        return None


def chat(messages, tools=None, temperature=0, think=False):
    """One model turn. Primary=Meterless(pinned Nemotron); fallback=direct NVIDIA."""
    kw = dict(messages=messages, temperature=temperature)
    if tools:
        kw["tools"] = tools
    if not think:
        kw["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

    errors = []
    if _meterless:
        try:
            comp = _meterless.chat.completions.create(model=PINNED_MODEL, **kw)
            return comp.choices[0].message, {"route": "meterless", "receipt_id": _receipt(comp), "model": PINNED_MODEL}
        except Exception as e:
            errors.append(f"meterless: {str(e)[:120]}")
    if _nvidia:
        try:
            comp = _nvidia.chat.completions.create(model=_NV_MODEL, **kw)
            return comp.choices[0].message, {"route": "nvidia-direct", "receipt_id": None, "model": _NV_MODEL}
        except Exception as e:
            errors.append(f"nvidia: {str(e)[:120]}")
    raise RuntimeError("No model route available — " + ("; ".join(errors) or "no providers configured"))
