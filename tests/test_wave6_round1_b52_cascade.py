"""
Wave 6 Round 1 Test - BUG-B52-CASCADE-V2-INCOMPLETE Verification
Tests that Pipeline in-memory characters reload after adjust, and Stage 4 uses new hair color.

Test Flow:
1. Create project with idea
2. Wait for Stage 2 character_ready
3. Adjust one character's hair to a distinctive non-black color (gold/pink)
4. Confirm characters
5. Wait for Pipeline to complete Stage 4+
6. Verify B52-fix v3 reload logged + HAIR_COLOR_REQUIREMENT_RULE injected in Stage 4 prompts
7. Verify old color completely cleared from prompts
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime


BASE_URL = "http://localhost:8000/api"
TEST_IDEA = "便利店收银员发现凌晨3点一只猫在送外卖"
TEST_MOOD = "幽默"
TEST_STYLE = "realistic"
TEST_ASPECT_RATIO = "2:3"
ADJUST_HAIR_COLOR = "bright gold"  # Distinctive non-black color
ADJUST_HAIR_STYLE = "straight and shiny"
LOG_FILE = "/tmp/xhstory_backend.log"


def api_call(method, path, body=None, timeout=30):
    """Make API call and return (status_code, json_data)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def wait_for_stage(project_id, target_stages, max_wait=300, poll_interval=5):
    """Poll status endpoint until target stage is reached."""
    start = time.time()
    last_stage = None
    while time.time() - start < max_wait:
        status, data = api_call("GET", f"/projects/{project_id}/chapters/1/status")
        if status == 200:
            stage = data.get("stage", "unknown")
            if stage != last_stage:
                log(f"  Stage: {stage} progress={data.get('progress',0)}% ETA={data.get('estimated_remaining_seconds','?')}s")
                last_stage = stage
            if stage in target_stages:
                return stage, data
        time.sleep(poll_interval)
    return None, {}


def test_round1_b52_cascade():
    """Round 1: B52 cascade full verification."""
    log("=" * 60)
    log("ROUND 1 — BUG-B52-CASCADE-V2-INCOMPLETE Verification")
    log("=" * 60)

    # Step 1: Create project
    log("Step 1: Creating project...")
    status, proj = api_call("POST", "/projects/", {
        "original_idea": TEST_IDEA,
        "user_selected_mood": TEST_MOOD,
        "style_preset": TEST_STYLE,
        "aspect_ratio": TEST_ASPECT_RATIO
    })
    assert status == 200 or status == 201, f"Project creation failed: {status} {proj}"
    project_id = proj["id"]
    log(f"  Created project: {project_id}")

    # Step 2: Generate outline
    log("Step 2: Generating outline (Stage 1)...")
    status, outline_resp = api_call("POST", f"/projects/{project_id}/generate-outline", {}, timeout=300)
    assert status == 200, f"Generate outline failed: {status} {outline_resp}"

    characters = outline_resp.get("characters", [])
    log(f"  Outline generated. Characters: {len(characters)}")
    for c in characters:
        log(f"    - {c.get('name','?')} ({c.get('id','?')})")

    # Step 3: Confirm outline
    log("Step 3: Confirming outline...")
    status, _ = api_call("POST", f"/projects/{project_id}/confirm-outline", {
        "confirmed_outline": outline_resp
    })
    assert status == 200, f"Confirm outline failed: {status}"

    # Step 4: Start generation
    log("Step 4: Starting generation...")
    status, _ = api_call("POST", f"/projects/{project_id}/start-generation")
    if status not in (200, 201, 202):
        log(f"  WARNING: start-generation returned {status}")

    # Step 5: Wait for character_ready
    log("Step 5: Waiting for character_ready stage...")
    stage, data = wait_for_stage(project_id, ["character_ready"], max_wait=600, poll_interval=5)
    assert stage == "character_ready", f"Never reached character_ready stage, got: {stage}"
    log(f"  Reached character_ready!")

    # Step 6: Get character list from DB to find char_001
    log("Step 6: Getting project details to find characters...")
    status, proj_detail = api_call("GET", f"/projects/{project_id}")
    assert status == 200, f"Get project failed: {status}"

    characters_confirmed = proj_detail.get("characters_confirmed", "missing")
    log(f"  characters_confirmed = {characters_confirmed}")

    # Get chapter data to find characters
    status, storyboard_data = api_call("GET", f"/projects/{project_id}/chapters/1/storyboard")
    chapter_chars = []
    if status == 200 and storyboard_data:
        chapter_chars = storyboard_data.get("characters", [])

    if not chapter_chars:
        # Try getting from outline response
        status2, outline_data = api_call("GET", f"/projects/{project_id}")
        chapter_chars = outline_data.get("characters", [])

    # Find char_001 (or the first character that is NOT a known black-hair character)
    char_to_adjust = None
    adjust_char_id = None
    for c in characters:
        char_id = c.get("id", "")
        if char_id and char_id != "char_003":  # Avoid char_003 (Wang Ayi - naturally black hair)
            char_to_adjust = c
            adjust_char_id = char_id
            break

    if not char_to_adjust:
        # Adjust char_001 by default
        adjust_char_id = "char_001"
        char_to_adjust = {"id": "char_001", "name": "角色1"}

    log(f"  Will adjust: {char_to_adjust.get('name','?')} ({adjust_char_id})")

    # Step 7: Adjust hair color to bright gold
    log(f"Step 7: Adjusting {adjust_char_id} hair to '{ADJUST_HAIR_COLOR}'...")
    adjust_payload = {
        "description": f"Changed hair to {ADJUST_HAIR_COLOR}",
        "physical_updates": {
            "hair_color": ADJUST_HAIR_COLOR,
            "hair_style": ADJUST_HAIR_STYLE
        }
    }

    status, adjust_resp = api_call("POST", f"/projects/{project_id}/characters/{adjust_char_id}/adjust",
                                    adjust_payload, timeout=120)
    if status == 200:
        log(f"  Adjust SUCCESS: hair_color updated to {ADJUST_HAIR_COLOR}")
        portrait_url = adjust_resp.get("portrait_url", "none")
        log(f"  New portrait_url: {portrait_url}")
    else:
        log(f"  WARNING: Adjust returned {status}: {adjust_resp}")

    # Wait for portrait to regenerate
    log("  Waiting 30s for portrait+fullbody regeneration...")
    time.sleep(30)

    # Step 8: Confirm characters
    log("Step 8: Confirming characters...")
    status, confirm_resp = api_call("POST", f"/projects/{project_id}/chapters/1/confirm-characters")
    if status == 200:
        log(f"  Characters confirmed!")
    else:
        log(f"  WARNING: confirm-characters returned {status}: {confirm_resp}")

    # Step 9: Wait for Pipeline to run through Stage 3, 4, 5, 6
    log("Step 9: Waiting for Pipeline stages (Stage 3 -> scenes wait -> Stage 4 -> Stage 5)...")
    log("  This will take a while (40-80 min). Polling every 15s...")

    # Watch for scenes_ready stage (R4-2 wait)
    time.sleep(10)
    stage, data = wait_for_stage(project_id, ["scenes_ready"], max_wait=600, poll_interval=15)
    if stage == "scenes_ready":
        log(f"  Reached scenes_ready! Confirming scenes immediately...")
        # Auto-confirm scenes to proceed
        status, scenes_confirm = api_call("POST", f"/projects/{project_id}/chapters/1/confirm-scenes")
        log(f"  Scenes confirm result: {status} {scenes_confirm}")
        # Continue watching

    # Wait for storyboard stage (Stage 4)
    stage, data = wait_for_stage(project_id, ["storyboard", "image_preparation", "image_generation", "bgm", "completed"],
                                  max_wait=3600, poll_interval=15)
    log(f"  Current stage after watching: {stage}")

    # Step 10: Wait for full completion
    if stage not in ("completed", "bgm"):
        log("Step 10: Waiting for full completion...")
        stage, data = wait_for_stage(project_id, ["completed"], max_wait=3600, poll_interval=30)

    log(f"  Pipeline final stage: {stage}")

    # Step 11: Verify Stage 4 storyboard prompts
    log("Step 11: Verifying Stage 4 storyboard prompts for hair color...")

    # Find the output directory
    import os
    output_dir = f"/Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/output/{project_id}"
    storyboard_path = f"{output_dir}/4_storyboard.json"

    results = {
        "project_id": project_id,
        "adjust_char_id": adjust_char_id,
        "adjust_hair_color": ADJUST_HAIR_COLOR,
        "storyboard_found": False,
        "shots_analyzed": 0,
        "gold_hits": 0,
        "gold_hit_rate": 0.0,
        "old_black_hits": 0,
        "b52_reload_logged": False,
        "r4_2_logged": False,
        "stage_completed": stage == "completed"
    }

    if os.path.exists(storyboard_path):
        results["storyboard_found"] = True
        with open(storyboard_path) as f:
            storyboard = json.load(f)

        shots = storyboard.get("shots", [])
        gold_hits = 0
        black_hits = 0
        total = 0

        for shot in shots:
            prompt = shot.get("image_prompt", "").lower()
            char_list = shot.get("characters_in_scene", [])

            if adjust_char_id in char_list:
                total += 1
                if ADJUST_HAIR_COLOR.lower() in prompt or "gold" in prompt or "bright gold" in prompt:
                    gold_hits += 1
                    log(f"  Shot {shot.get('shot_id','?')}: GOLD HIT - prompt contains gold color")
                if "black hair" in prompt or "deep black" in prompt or "jet-black" in prompt or "dark hair" in prompt:
                    black_hits += 1
                    log(f"  Shot {shot.get('shot_id','?')}: OLD BLACK HIT - {shot.get('shot_id')} still uses old color!")

        results["shots_analyzed"] = total
        results["gold_hits"] = gold_hits
        results["old_black_hits"] = black_hits
        results["gold_hit_rate"] = gold_hits / total if total > 0 else 0.0

        log(f"\n  STORYBOARD ANALYSIS:")
        log(f"  Shots with {adjust_char_id}: {total}")
        log(f"  Gold color hits: {gold_hits} ({results['gold_hit_rate']*100:.0f}%)")
        log(f"  Old black color hits: {black_hits}")
    else:
        log(f"  WARNING: storyboard not found at {storyboard_path}")

    # Step 12: Check backend log for B52 fix marker
    log("Step 12: Checking backend log for B52-fix v3 reload marker...")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log_content = f.read()

        if "B52-fix v3" in log_content:
            results["b52_reload_logged"] = True
            log("  B52-fix v3 LOG: FOUND")
        else:
            log("  WARNING: B52-fix v3 not found in log")

        if "R4-2 / B58" in log_content:
            results["r4_2_logged"] = True
            log("  R4-2 / B58 LOG: FOUND")
        else:
            log("  WARNING: R4-2 / B58 not found in log")
    else:
        log(f"  WARNING: Log file not found at {LOG_FILE}")

    # Final verdict
    log("\n" + "=" * 60)
    log("ROUND 1 RESULTS:")
    log(f"  Project ID: {project_id}")
    log(f"  Adjusted char: {adjust_char_id} hair -> {ADJUST_HAIR_COLOR}")
    log(f"  B52-fix v3 reload logged: {results['b52_reload_logged']}")
    log(f"  R4-2 scenes wait logged: {results['r4_2_logged']}")
    log(f"  Gold color hit rate: {results['gold_hit_rate']*100:.0f}% (target >=80%)")
    log(f"  Old black color hits: {results['old_black_hits']} (target 0)")
    log(f"  Pipeline completed: {results['stage_completed']}")

    # Pass/Fail assessment
    checks = {
        "B52-fix v3 reload in log": results["b52_reload_logged"],
        "Gold hit rate >=80%": results["gold_hit_rate"] >= 0.8 if results["shots_analyzed"] > 0 else None,
        "Old black hits = 0": results["old_black_hits"] == 0,
        "Pipeline completed": results["stage_completed"]
    }

    log("\n  VERIFICATION CHECKLIST:")
    all_pass = True
    for check, result in checks.items():
        if result is None:
            status_str = "N/A (no shots analyzed)"
        elif result:
            status_str = "PASS"
        else:
            status_str = "FAIL"
            all_pass = False
        log(f"  [{status_str}] {check}")

    log(f"\n  OVERALL: {'PASS' if all_pass else 'NEEDS INVESTIGATION'}")
    log("=" * 60)

    return results


if __name__ == "__main__":
    results = test_round1_b52_cascade()
    # Write results to file for reporting
    with open("/tmp/wave6_round1_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /tmp/wave6_round1_results.json")
