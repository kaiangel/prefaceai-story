"""
Style drift probe (AI-ML Wave 12 P1) — temporary validation harness.

Generates a portrait of a STRONG anime-prior character (young handsome man)
for high-risk styles, using the EXACT StyleEnforcer.enforce_prompt path that
ReferenceImageManager._build_portrait_prompt uses (mandatory[:5] / forbidden[:8]
mandatory-prefix). Tests current vs patched forbidden/mandatory keyword lists.

Usage:
    venv/bin/python3 scripts/style_drift_probe.py <style1> <style2> ...

Output: test_output/manualtest/style_drift_probe/<style>_<label>.png
This script is read-only w.r.t. style_enforcer.py — it reads the live config.
"""
import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.style_enforcer import StyleEnforcer
from app.services.seedream_generator import _call_seedream_sync

OUT_DIR = Path("test_output/manualtest/style_drift_probe")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Strongest anime-prior trigger from test26 (陈明): young handsome man.
# Same core_prompt shape RIM._build_portrait_prompt produces (minus Layer 1 anchor,
# which only RE-STATES the same top5/top8 — so the mandatory prefix is the decisive test).
CORE_PROMPT = (
    "Portrait of Chen Ming, a 28-year-old handsome young man, sharp jawline, "
    "clean short black hair, confident gaze, slim athletic build, "
    "wearing a fitted dark jacket. Head-and-shoulders framing, neutral expression, "
    "looking slightly off-camera. Clean studio-like background appropriate to the style."
)

ASPECT = "2:3"


def gen(style: str, label: str) -> dict:
    enforced = StyleEnforcer.enforce_prompt(CORE_PROMPT, style, add_quality_suffix=True)
    api_key = os.getenv("ARK_API_KEY", "").strip()
    t0 = time.time()
    res = _call_seedream_sync(enforced, [], ASPECT, api_key)
    dt = time.time() - t0
    ok = res.get("success")
    if ok and res.get("pil_image") is not None:
        path = OUT_DIR / f"{style}_{label}.png"
        res["pil_image"].save(path)
        print(f"  [{style}/{label}] OK {dt:.1f}s -> {path}")
        return {"style": style, "label": label, "ok": True, "path": str(path), "sec": round(dt, 1)}
    print(f"  [{style}/{label}] FAIL {dt:.1f}s err={res.get('error')} kind={res.get('error_kind')}")
    return {"style": style, "label": label, "ok": False, "err": res.get("error"), "kind": res.get("error_kind")}


if __name__ == "__main__":
    styles = sys.argv[1:] or ["cyberpunk"]
    results = []
    for s in styles:
        enf = StyleEnforcer.get_enforcement(s)
        print(f"\n=== {s} ===")
        print(f"  mandatory[:5]={enf.mandatory_keywords[:5]}")
        print(f"  forbidden[:8]={enf.forbidden_keywords[:8]}")
        results.append(gen(s, "current"))
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults -> {OUT_DIR/'results.json'}")
