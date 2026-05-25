// useETA — RISK-T17-5 (Wave 11.3) + RISK-T20-2 (Wave 15) + RISK-T20-9 (Wave 16/17) + T20-44 (2026-05-20) frontend ETA hook
//
// Purpose: stable ETA display for the StageC generation progress screen.
//
// Problem being fixed (original, RISK-T17-5):
//   - backend `estimated_remaining_seconds` is null most of the time (Wave 11.3 backend fixes this)
//   - frontend fallback = linear extrapolation from startTimeRef, which jumps wildly when
//     progress is low (e.g. 10%: small elapsed → huge total → large remaining swings)
//   - when stage changes, `lastEtaSecondsRef` resets (Wave 9 RISK-T15-7 fix) but
//     `backendEstimatedSecondsRef` also clears, so the jumpy fallback immediately fires
//
// Additional bugs fixed (RISK-T20-2, Wave 15):
//   Bug 1 — Stage transition hard-cut: ETA used to jump -5 min / -4 min at stage boundaries
//            (e.g. Stage 4→5: 12 min → 8 min instantly). Fix: sliding-window smoothing — on
//            stage transition we record prevEtaSec and blend toward new-stage budget gradually,
//            moving at most MAX_STEP_PER_POLL (3 s) per 2-s poll cycle.
//   Bug 2 — ETA disappears at 0: monotonicity guard drives rawSec to 0 →
//            Math.ceil(0/60)=0 → etaText=null → the ETA indicator vanishes.
//            Fix: rawSec <= 0 → "即将完成"; rawSec < 60 → "还需不到 1 分钟".
//   Bug 3 — "正在收尾" based on elapsed time (RISK-NEW-1 side-effect): showed "收尾" when
//            elapsed >= 30 min even if 4 shots were still generating (test18 11:07 incident).
//            Fix: remove elapsed-time trigger; use stage + progress-based detection instead.
//
// RISK-T20-9 (Wave 16): Backend authoritative ETA — hardcoded budget fix
//   Root cause: STAGE_BUDGET_SECONDS[image_generation] = 1440 (worst-case 29 shots hardcoded).
//   When actual shot count < 29 (e.g. 19 shots), ETA is ~100% too fast:
//     budget 1440s vs actual ~380s → ETA reaches 0 when 5+ min still remaining.
//   Fix: prioritise backend `estimatedRemainingSeconds` (dynamically calculated from
//   actual_shot_count × 60 / max_concurrent by Backend's estimate_remaining() function).
//
// RISK-T20-9 v3 (Wave 17): Full ETA algorithm rework
//   Changes:
//   1. Delete message regex parsing ("已生成 X/Y") — backend now provides shots_total /
//      shots_completed / shots_failed directly (STATUS_API_CONTRACT v1.1 §1.2).
//   2. Frontend fallback algorithm (when backend ETA null):
//      remaining = (shots_total - shots_completed) * per_shot_real / max_concurrent
//      per_shot_real = sliding-window real average of actual per-shot timing (fallback: 80s)
//      max_concurrent = 3 (IMAGE_MAX_CONCURRENT, matching backend config)
//   3. Stage 5 → Stage 6 BGM accumulation: when entering bgm stage, add BGM_BUDGET_SECONDS
//      (180s) to remaining so ETA doesn't jump from "3 min" to "0 min" at transition.
//   4. Terminal UX fix: progress >= 95% still shows concrete ETA number (NOT "正在收尾").
//      Only completed=true (stage=completed or progress>=100) triggers "故事生成完成".
//      "正在收尾" is removed — it caused the "78% → 即将完成 → no ETA" bug.
//
// Priority chain (Wave 17 / T20-44):
//   1. estimatedRemainingSeconds (backend authoritative, >= 0 accepted)     ← top priority
//      T20-44: When P1 is active, monotonicity guard and upward smoothing
//              are BYPASSED — backend ETA is shown directly (CONTRACT v1.3 §1.4).
//   2. shots_total / shots_completed frontend formula                        ← T20-9.v3 fallback
//   3. backendEtaSec (legacy field, > 0 only)                               ← backward compat
//   4. STAGE_BUDGET_SECONDS fallback (hardcoded, last resort)
//
// Usage:
//   const { etaText } = useETA({ stage, progress, estimatedRemainingSeconds,
//                                 shotsTotal, shotsCompleted });
//
// shots_total / shots_completed contract (STATUS_API_CONTRACT v1.1):
//   - non-null during image_generation stage (Backend T20-13 landed)
//   - null before Stage 4 completes or after stage=completed
//   Frontend uses them for fallback ETA when backend estimatedRemainingSeconds is null.

import { useRef, useCallback, useEffect } from "react";

// ---------------------------------------------------------------------------
// Stage-based ETA budgets (seconds remaining at start of each stage)
// Calibrated from test18 empirical data (2026-05-14):
//   - story_generation ~2 min, character_design ~1.5 min
//   - screenplay ~4 min (10 scenes), storyboard ~3.5 min (Stage 4)
//   - image_preparation ~3 min (portrait serial + scene refs)
//   - image_generation: shot_count * avg_per_shot / max_concurrent
//     test18: 29 shots × 100s / 3 concurrency ≈ 967s (~16 min)
//   - bgm ~50s
// These are UPPER BOUNDS — actual ETA shrinks as progress advances within stage.
// ---------------------------------------------------------------------------
const STAGE_BUDGET_SECONDS: Record<string, number> = {
  story_generation: 120,       // ~2 min
  character_design: 90,        // ~1.5 min
  character_ready: 0,          // transition, no wait
  screenplay: 240,             // ~4 min (10 scenes)
  scenes_ready: 0,             // transition checkpoint
  storyboard: 210,             // ~3.5 min (Stage 4)
  // T21-NEW-7 (2026-05-21 DEC-047 v1.4): Stage 4.5 场景参考图生成 baseline.
  //   Backend STAGE_DURATIONS["scene_image_preparation"] = 180s
  //   (与 pipeline_orchestrator.py L82 + STATUS_API_CONTRACT v1.4 同步).
  //   实测: 3 location × interior+exterior = 6 张 Seedream, ~30s/张 = ~180s.
  scene_image_preparation: 180,
  // T21-NEW-7 v1.4: scene_references_ready 是 R4-3 等用户确认稳态, ETA=0 不显示 (与 character_ready/scenes_ready 一致).
  scene_references_ready: 0,
  image_preparation: 180,      // ~3 min (portrait × 3 serial + scene refs × 3)
  image_generation: 1440,      // ~24 min (worst-case 29 shots, conservative)
  bgm: 180,                    // ~3 min (Mureka generation, empirical test17v2: 64s + buffer)
  music: 180,                  // alias
  completed: 0,
};

// T20-9.v3: Default per-shot time (seconds) for frontend fallback formula.
// Based on test17v2 median: ~130s / max_concurrent=3 → ~43s effective.
// But using raw per-shot = 80s (empirical median single-shot, not divided by concurrency).
// The formula divides by max_concurrent separately.
const DEFAULT_PER_SHOT_SEC = 80;

// T20-9.v3: Max concurrent image generation jobs (matches backend IMAGE_MAX_CONCURRENT=3)
const MAX_CONCURRENT = 3;

// T20-9.v3: Sliding window size for per-shot real average.
// We track the last N shot completions to estimate per_shot_real.
const SHOT_TIMING_WINDOW = 5;

// Stages where we deliberately do NOT show ETA (user is reviewing, not waiting for compute).
// T21-NEW-7 (2026-05-21 DEC-047 v1.4): scene_references_ready 加入 — R4-3 闸门,
// 用户在 /scenes 看真场景参考图 + 60s 倒计时, ETA 不该显示在那个页面 (与 character_ready 对偶).
const REVIEW_STAGES = new Set([
  "character_ready",
  "scenes_ready",
  "scene_references_ready",
  "completed",
]);

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

export interface UseETAInput {
  /** Current backend stage string (e.g. "image_generation") */
  stage: string | null;
  /** Current backend progress 0-100 */
  progress: number;
  /**
   * RISK-T20-9 (Wave 16): Backend authoritative ETA in seconds.
   * Dynamically calculated from actual shot count (not hardcoded worst-case budget).
   * Accepts >= 0 (includes zero = "almost done"). Takes top priority.
   * Set from status.estimated_remaining_seconds after T20-9 backend fix lands.
   */
  estimatedRemainingSeconds?: number | null;
  /**
   * RISK-T20-9 v3 (Wave 17): Total shot count from backend.
   * STATUS_API_CONTRACT v1.1 §1.2: shots_total (number | null)
   * Non-null during image_generation stage after Stage 4 completes.
   * Used for frontend fallback ETA formula: (shots_total - shots_completed) * per_shot / concurrent
   */
  shotsTotal?: number | null;
  /**
   * RISK-T20-9 v3 (Wave 17): Completed shot count from backend.
   * STATUS_API_CONTRACT v1.1 §1.2: shots_completed (number | null)
   * "Completed" means succeeded + failed combined (i.e. no longer in-flight).
   * Non-null during image_generation stage.
   */
  shotsCompleted?: number | null;
  /**
   * RISK-T20-9 v3 (Wave 17): Failed shot count from backend.
   * STATUS_API_CONTRACT v1.1 §1.2: shots_failed (number | null)
   * Used for display only (we don't exclude failed from ETA — they're already counted).
   */
  shotsFailed?: number | null;
  /**
   * Legacy field — backend-provided ETA in seconds from older implementation.
   * Kept for backward compatibility. Only used when estimatedRemainingSeconds is null
   * and shots_total/shots_completed are also unavailable.
   * Accepts > 0 only (zero is ignored to avoid premature "done" display).
   * @deprecated Prefer estimatedRemainingSeconds (top priority field, RISK-T20-9).
   */
  backendEtaSec?: number | null | undefined;
  /**
   * RISK-NEW-1 (now superseded by Bug 3 fix in RISK-T20-2):
   * Backend-provided actual elapsed seconds since job started.
   * Kept in the interface for backward-compatibility — IGNORED in current implementation.
   */
  actualElapsedSec?: number | null;
}

export interface UseETAOutput {
  /** Human-readable ETA string, e.g. "预计还需约 8 分钟" or null when unknown */
  etaText: string | null;
  /** Raw ETA seconds (rounded), for testing / logging */
  etaSeconds: number | null;
}

// ---------------------------------------------------------------------------
// Hook implementation
// ---------------------------------------------------------------------------

// RISK-T20-2 Bug 1: max ETA delta per poll cycle for sliding-window smoothing.
// Poll interval is 2s; we allow at most 3s movement per cycle so a 5-min jump
// takes ~(300s/3s) * 2s = 200s ≈ 3 min to fully converge — smooth from user POV.
const MAX_STEP_PER_POLL = 3; // seconds

// RISK-T20-2 Bug 2: near-zero ETA thresholds
const NEAR_ZERO_SEC = 60; // show "还需不到 1 分钟" when rawSec < 60

export function useETA({ stage, progress, estimatedRemainingSeconds, shotsTotal, shotsCompleted, backendEtaSec }: UseETAInput): UseETAOutput {
  // Track stage-start time so we can compute elapsed within current stage
  const stageStartTimeRef = useRef<number>(Date.now());
  // The stage-budget at stage-start (used for within-stage linear decay)
  const stageBudgetRef = useRef<number | null>(null);
  // Monotonicity guard: ETA only decreases within a stage
  const lastEtaSecRef = useRef<number | null>(null);
  // Previous stage so we can detect transitions
  const prevStageRef = useRef<string | null>(null);
  // RISK-T20-2 Bug 1: ETA value from previous render — used for sliding-window smoothing
  const prevEtaSecRef = useRef<number | null>(null);
  // T20-9.v3: Sliding window of actual per-shot timing observations (seconds per shot).
  // We record the timestamp each time shotsCompleted increments.
  const shotTimestampsRef = useRef<number[]>([]); // timestamps when each shot completed
  const prevShotsCompletedRef = useRef<number | null>(null); // track increments

  // P2-2 (Wave 12): time-interpolation of the backend authoritative ETA.
  // Problem (test26): in Stage 1-4 the backend ETA `_calculate_eta_with_progress(stage, progress)`
  // is FROZEN whenever stage/progress are frozen (single LLM call, no sub-progress). The display
  // then sits at e.g. "30 分钟" for a long time → user thinks it's stuck.
  // Fix: anchor the last backend value + the wall-clock time we first saw it, then interpolate
  // downward by elapsed seconds between backend updates. When a NEW backend value arrives we
  // recalibrate the anchor (handles both Stage 1-4 freeze and stage-transition jumps).
  // This does NOT replace the backend-authoritative priority (T20-9) — it only smooths the
  // *display* of that same value between polls so it ticks down instead of freezing.
  const anchorBackendEtaRef = useRef<number | null>(null); // last raw backend value seen
  const anchorBackendTsRef = useRef<number | null>(null);  // wall-clock ms when that value first appeared

  // Reset ETA state whenever stage changes
  const resetForStage = useCallback((newStage: string | null) => {
    stageStartTimeRef.current = Date.now();
    lastEtaSecRef.current = null;
    // T20-9.v3: reset shot timing window on stage transition
    shotTimestampsRef.current = [];
    prevShotsCompletedRef.current = null;
    // P2-2: reset the backend-ETA interpolation anchor on stage transition so the next
    // backend value re-anchors cleanly (a new stage's ETA may jump up legitimately).
    anchorBackendEtaRef.current = null;
    anchorBackendTsRef.current = null;
    // Bug 1: On stage transition, we DON'T reset prevEtaSecRef — we keep the last
    // displayed ETA so the sliding window can smoothly blend from it toward the new
    // stage budget. This prevents the hard-cut jump (e.g. 12 min → 8 min instantly).
    if (newStage && !REVIEW_STAGES.has(newStage)) {
      stageBudgetRef.current = STAGE_BUDGET_SECONDS[newStage] ?? null;
    } else {
      stageBudgetRef.current = null;
    }
    // eslint-disable-next-line no-console
    console.log(
      "[useETA] T20-9.v3: stage transition →",
      newStage,
      "| reset ETA state | budget =",
      stageBudgetRef.current,
      "s",
    );
  }, []);

  // Detect stage change and reset (useEffect to avoid side-effects during render)
  useEffect(() => {
    if (prevStageRef.current !== stage) {
      resetForStage(stage);
      prevStageRef.current = stage;
    }
  }, [stage, resetForStage]);

  // -------------------------------------------------------------------------
  // Compute ETA — pure calculation, called each render
  // -------------------------------------------------------------------------

  // Return null for review stages or completed
  if (!stage || REVIEW_STAGES.has(stage) || progress >= 100) {
    prevEtaSecRef.current = null;
    return { etaText: null, etaSeconds: null };
  }

  // T20-9.v3: Update shot timing window when shotsCompleted increments.
  // We record a timestamp for each newly completed shot so we can compute
  // per_shot_real = (elapsed since first shot in window) / (shots in window).
  // This runs synchronously during render (refs only, no setState).
  if (
    stage === "image_generation" &&
    typeof shotsCompleted === "number" &&
    shotsCompleted > 0
  ) {
    const prev = prevShotsCompletedRef.current;
    if (prev === null || shotsCompleted > prev) {
      // New shots completed since last render — record one timestamp per new shot
      const newCount = prev === null ? shotsCompleted : shotsCompleted - prev;
      const now = Date.now();
      for (let i = 0; i < newCount; i++) {
        shotTimestampsRef.current.push(now);
      }
      // Keep only last SHOT_TIMING_WINDOW entries
      if (shotTimestampsRef.current.length > SHOT_TIMING_WINDOW) {
        shotTimestampsRef.current = shotTimestampsRef.current.slice(
          shotTimestampsRef.current.length - SHOT_TIMING_WINDOW,
        );
      }
      prevShotsCompletedRef.current = shotsCompleted;
    }
  }

  // Compute per_shot_real from sliding window.
  // If we have >= 2 timestamps: elapsed = last - first; per_shot = elapsed / (window size - 1)
  // Minimum 2 data points needed to compute a meaningful rate.
  let perShotReal = DEFAULT_PER_SHOT_SEC;
  const timestamps = shotTimestampsRef.current;
  if (timestamps.length >= 2) {
    const windowElapsedSec = (timestamps[timestamps.length - 1] - timestamps[0]) / 1000;
    const windowShots = timestamps.length - 1; // intervals between timestamps
    if (windowElapsedSec > 0 && windowShots > 0) {
      perShotReal = windowElapsedSec / windowShots;
      // Cap to avoid extreme outliers (e.g. Shot 16's 851s) from inflating ETA unboundedly
      perShotReal = Math.min(perShotReal, 600); // cap at 10 min per shot
      perShotReal = Math.max(perShotReal, 20);  // floor at 20s per shot
    }
  }

  // Priority chain (T20-9.v3 Wave 17 / T20-44):
  //   1. estimatedRemainingSeconds — backend authoritative (dynamic, >= 0 accepted)
  //   2. shots_total / shots_completed — frontend formula (T20-9.v3 new fallback)
  //   3. backendEtaSec — legacy field (> 0 only, backward compat)
  //   4. STAGE_BUDGET_SECONDS fallback — hardcoded, last resort
  let rawSec: number | null = null;
  // T20-44: Track whether P1 (backend authoritative) is the active source.
  // When true, skip monotonicity guard and upward-smoothing so that
  // backend ETA (e.g. 790s) is shown immediately, not clamped by stale local state.
  // STATUS_API_CONTRACT v1.3 §1.4: "Frontend 直接读 backend estimated_remaining_seconds 即可".
  let isBackendAuthoritative = false;

  if (typeof estimatedRemainingSeconds === "number" && estimatedRemainingSeconds >= 0) {
    // 1. Backend authoritative — dynamic estimate from actual shot count / stage budget.
    //    Accepts >= 0 (zero = "almost done" is valid).
    isBackendAuthoritative = true;

    // P2-2: time-interpolation. If the backend value CHANGED since last render, re-anchor
    // (handles Stage 1-4 freeze recalibration + stage-transition jumps). Otherwise interpolate
    // downward from the anchor by wall-clock elapsed so a frozen backend value still ticks down.
    const now = Date.now();
    const anchorVal = anchorBackendEtaRef.current;
    if (anchorVal === null || anchorVal !== estimatedRemainingSeconds) {
      // New (or first) backend value → recalibrate the anchor.
      anchorBackendEtaRef.current = estimatedRemainingSeconds;
      anchorBackendTsRef.current = now;
      rawSec = estimatedRemainingSeconds;
    } else {
      // Same backend value as before (frozen) → interpolate down by elapsed since anchor.
      const elapsedSinceAnchorSec = anchorBackendTsRef.current !== null
        ? (now - anchorBackendTsRef.current) / 1000
        : 0;
      const interpolated = estimatedRemainingSeconds - elapsedSinceAnchorSec;
      // Floor at NEAR_ZERO_SEC so a frozen backend value can't prematurely show "即将完成"
      // during Stage 1-4. Once the real backend value drops below NEAR_ZERO, that new (smaller)
      // value re-anchors via the branch above and we honour it verbatim.
      rawSec = Math.max(interpolated, Math.min(estimatedRemainingSeconds, NEAR_ZERO_SEC));
    }
  } else if (
    stage === "image_generation" &&
    typeof shotsTotal === "number" &&
    shotsTotal > 0 &&
    typeof shotsCompleted === "number" &&
    shotsCompleted >= 0
  ) {
    // 2. T20-9.v3: Frontend fallback formula using shots_total / shots_completed.
    //    remaining = (shots_total - shots_completed) * per_shot_real / max_concurrent
    //    This replaces the old "已生成 X/Y" message regex parse path.
    const remainingShots = Math.max(0, shotsTotal - shotsCompleted);
    rawSec = (remainingShots * perShotReal) / MAX_CONCURRENT;
    // eslint-disable-next-line no-console
    console.log(
      "[useETA] T20-9.v3 fallback: remaining shots =", remainingShots,
      "| per_shot_real =", Math.round(perShotReal), "s",
      "| concurrent =", MAX_CONCURRENT,
      "| rawSec =", Math.round(rawSec), "s",
    );
  } else if (typeof backendEtaSec === "number" && backendEtaSec > 0) {
    // 3. Legacy backendEtaSec — kept for backward compat.
    rawSec = backendEtaSec;
  } else {
    // 4. Fallback: stage-budget minus elapsed time within current stage.
    // Last resort — gives wrong ETA for image_generation when shot count < 29.
    // Only reached when backend provides no ETA data at all.
    const budget = stageBudgetRef.current;
    if (budget !== null && budget > 0) {
      const elapsedInStage = (Date.now() - stageStartTimeRef.current) / 1000;
      const remaining = budget - elapsedInStage;
      rawSec = remaining > 0 ? remaining : 0;
    }
    // If no budget (unknown stage), return null rather than a wild guess
  }

  // T20-9.v3: Stage 5 → Stage 6 BGM transition.
  // T20-44: When backend provides ETA (P1 active), this transition is handled transparently —
  // backend _compute_v3_eta() switches to bgm baseline formula (chapters.py).
  // Frontend reads backend ETA directly (isBackendAuthoritative=true bypasses smoothing).
  // BGM budget = 180s in STAGE_BUDGET_SECONDS[bgm] — only used as P4 fallback.

  if (rawSec === null) {
    prevEtaSecRef.current = null;
    return { etaText: null, etaSeconds: null };
  }

  // Cap at 30 min, floor at 0
  rawSec = Math.min(rawSec, 30 * 60);
  rawSec = Math.max(rawSec, 0);

  // T20-44: When backend provides authoritative ETA (P1 active), bypass monotonicity
  // guard and upward-smoothing. The backend's computed value should be shown directly.
  // STATUS_API_CONTRACT v1.3 §1.4: "Frontend 直接读 backend estimated_remaining_seconds 即可".
  // Root cause of test20 "3分钟" display: prev ETA was ~180s (BGM budget fallback),
  // then image_generation started with backend ETA=790s. The upward clamp at
  // "if (rawSec > prevEta) rawSec = prevEta - EPSILON" drove 790 → 180 → 3 min display.
  if (isBackendAuthoritative) {
    // Directly use backend ETA — update refs for future monotonicity tracking.
    lastEtaSecRef.current = rawSec;
    prevEtaSecRef.current = rawSec;
    // (fall through to display formatting)
  } else {
    // 3. Monotonicity guard within current stage — ETA never increases
    //    (a new fallback/budget value > lastEta is clamped down)
    //    Use EPSILON = 1.5s to ensure visible descent each poll cycle (2s interval)
    const FALLBACK_EPSILON = 1.5;
    const last = lastEtaSecRef.current;
    if (last !== null) {
      const cap = last - FALLBACK_EPSILON;
      if (rawSec > cap) rawSec = cap;
    }
    rawSec = Math.max(rawSec, 0);
    lastEtaSecRef.current = rawSec;

    // RISK-T20-2 Bug 1: Sliding-window smoothing across stage transitions.
    // After a stage switch, the new stage's rawSec may be very different from the
    // previous ETA (e.g. storyboard just finished at 12 min, image_generation budget
    // starts at 24 min but we only want to show ~8 min left). Without smoothing this
    // causes a sudden jump. We limit the per-render movement to MAX_STEP_PER_POLL.
    // Note: smoothing only LIMITS upward movement — downward movement is already
    // controlled by the monotonicity guard above. We need to also limit big downward
    // jumps at stage transition points.
    const prevEta = prevEtaSecRef.current;
    if (prevEta !== null) {
      const delta = prevEta - rawSec; // positive = rawSec dropped (normal)
      if (delta > MAX_STEP_PER_POLL) {
        // Clamp the drop to MAX_STEP_PER_POLL per render cycle
        rawSec = prevEta - MAX_STEP_PER_POLL;
      }
      // Note: if rawSec > prevEta (shouldn't happen often due to monotonicity guard,
      // but can occur on stage transitions when new budget > prevEta), we allow it
      // to avoid ETA jumping UP — clamp to prevEta instead.
      if (rawSec > prevEta) {
        rawSec = prevEta - FALLBACK_EPSILON; // treat like any other monotonicity violation
      }
    }
    rawSec = Math.max(rawSec, 0);
    prevEtaSecRef.current = rawSec;
  }

  const etaSeconds = Math.round(rawSec);

  // T20-9.v3 Terminal UX fix (Founder feedback: "78% → 即将完成 → no ETA number"):
  // - progress >= 95% → still show concrete ETA number (not "正在收尾")
  // - "正在收尾" is REMOVED — it caused ETA to disappear too early
  // - Only progress >= 100 or stage=completed shows "故事生成完成" (via the REVIEW_STAGES
  //   early-return at the top of this function)
  // Display: "即将完成" only when rawSec truly reaches 0.
  // Display: "还需不到 1 分钟" when rawSec < 60s.
  // Display: "预计还需约 N 分钟" for all other cases (including progress >= 95%).

  // RISK-T20-2 Bug 2: ETA near zero — show reassuring text instead of disappearing.
  if (rawSec <= 0) {
    return { etaText: "即将完成", etaSeconds: 0 };
  }
  if (rawSec < NEAR_ZERO_SEC) {
    return { etaText: "还需不到 1 分钟", etaSeconds };
  }

  // Convert to display string — always show concrete number regardless of progress %
  const minutes = Math.ceil(rawSec / 60);
  const etaText = `预计还需约 ${minutes} 分钟`;

  return { etaText, etaSeconds };
}
