"""Model provider: Meterless Nightshift (primary, pinned Nemotron) with direct-NVIDIA fallback.

chat() returns (message, meta). meta = {route, receipt_id, routed_model, usage, model, fallback_reason?}.
The Meterless receipt (routed_model/cost) is captured for the Sponsor-tech story + DGX prize;
a fallback_reason is recorded when Meterless is unreachable so we never silently lose the route.
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


def _meterless_meta(comp):
    try:
        m = comp.model_dump().get("meterless") or {}
    except Exception:
        m = {}
    return {"receipt_id": m.get("receipt_id"), "routed_model": m.get("routed_model")}


def _usage(comp):
    try:
        u = comp.usage
        return {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
                "total_tokens": u.total_tokens}
    except Exception:
        return {}


def chat(messages, tools=None, temperature=0, think=False, require_meterless=False):
    """One model turn. Primary=Meterless(pinned Nemotron); fallback=direct NVIDIA unless require_meterless."""
    kw = dict(messages=messages, temperature=temperature)
    if tools:
        kw["tools"] = tools
    if not think:
        kw["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

    fallback_reason = None
    if _meterless:
        try:
            comp = _meterless.chat.completions.create(model=PINNED_MODEL, **kw)
            meta = {"route": "meterless", "model": PINNED_MODEL, "usage": _usage(comp), **_meterless_meta(comp)}
            return comp.choices[0].message, meta
        except Exception as e:
            fallback_reason = f"meterless unreachable: {str(e)[:120]}"
            if require_meterless:
                raise RuntimeError(fallback_reason)
    if _nvidia:
        comp = _nvidia.chat.completions.create(model=_NV_MODEL, **kw)
        return comp.choices[0].message, {"route": "nvidia-direct", "model": _NV_MODEL,
                                         "usage": _usage(comp), "receipt_id": None,
                                         "routed_model": _NV_MODEL, "fallback_reason": fallback_reason}
    raise RuntimeError("No model route available — " + (fallback_reason or "no providers configured"))
