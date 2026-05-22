/**
 * UX-16: URL routing utilities for the /create flow.
 *
 * Maps between (CreateStage + GenerationSubPhase) and URL `[stage]` segment.
 * Single dynamic route shape: /create/[projectUuid]/[stage]
 *
 * URL stages (6):
 *   - outline    → confirm stage  (StageB)
 *   - characters → generate / char-preview  (StageC sub-phase char-preview)
 *   - scenes     → generate / scene-preview (StageC sub-phase scene-preview)
 *   - generating → generate / text-gen | shot-gen (StageC waiting screens)
 *   - preview    → preview (StageD)
 *   - delivery   → deliver (StageE)
 *
 * Why one route segment instead of nested routes for each backend stage?
 * - story_generation / character_design / character_ready (early) / screenplay /
 *   storyboard / image_preparation / image_generation / bgm are all "AI is working,
 *   user waits" — semantically a single URL `/generating` is correct UX.
 * - char-preview & scene-preview are real user checkpoints (StageC asks user to
 *   confirm characters / scenes), so they need their own URL.
 * - 6 segments hit the sweet spot of "URL is meaningful for sharing + back-button
 *   maps to a real semantic step" without exploding into 10+ nested routes.
 *
 * Loading/restoration policy when URL [stage] conflicts with backend status:
 *   Backend status is the source of truth.
 *   - status === "completed" → force /preview (URL [generating | outline | characters | scenes] is stale)
 *   - status === "generating" with stage in [story_generation, character_design] → /generating
 *   - status === "generating" with stage === character_ready → /characters (if not yet confirmed)
 *   - status === "generating" with stage in [screenplay, storyboard, image_preparation,
 *     image_generation, bgm] → /generating
 *   - status === "pending" / no job → /outline (user has not confirmed outline yet)
 *   - URL [delivery] is allowed only when backend completed AND user has visited /preview first
 *
 * URL-state feedback loop avoidance:
 *   - state → URL: useEffect on (currentStage, generationSubPhase) calls router.replace
 *   - URL → state: useEffect on params.stage compares with derivedUrlStage; only dispatches if mismatch
 *   - lastPushedUrlRef tracks the URL we pushed so we can ignore the echoing pathname change
 */

import type { CreateStage, GenerationSubPhase } from "@/types/create";

export type UrlStage =
  | "outline"
  | "characters"
  | "scenes"
  | "generating"
  | "preview"
  | "delivery";

export const URL_STAGES: readonly UrlStage[] = [
  "outline",
  "characters",
  "scenes",
  "generating",
  "preview",
  "delivery",
] as const;

export function isUrlStage(value: string | undefined | null): value is UrlStage {
  return !!value && (URL_STAGES as readonly string[]).includes(value);
}

/**
 * Compute the URL [stage] segment from current React state.
 * This is the "state → URL" direction.
 */
export function deriveUrlStageFromState(
  currentStage: CreateStage,
  subPhase: GenerationSubPhase
): UrlStage | null {
  switch (currentStage) {
    case "input":
      return null; // /create has no [uuid] yet (project not created)
    case "confirm":
      return "outline";
    case "generate":
      if (subPhase === "char-preview") return "characters";
      // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene-preview → scenes 映射已移除.
      //   Pipeline 直接 Stage 3 → Stage 4, 不再有文字层场景确认闸门.
      // T21-NEW-7 (2026-05-21 DEC-047 v1.4): scene-refs-preview 复用 /scenes URL 段.
      //   scene-refs-preview → SceneRefsPreview (R4-3 真场景参考图视觉确认, 保留)
      if (subPhase === "scene-refs-preview") return "scenes";
      return "generating"; // text-gen / shot-gen / unknown
    case "preview":
      return "preview";
    case "deliver":
      return "delivery";
    default:
      return null;
  }
}

/**
 * Map URL [stage] segment back to (CreateStage, GenerationSubPhase).
 * This is the "URL → state" direction.
 */
export function stateFromUrlStage(urlStage: UrlStage): {
  currentStage: CreateStage;
  subPhase: GenerationSubPhase | null;
} {
  switch (urlStage) {
    case "outline":
      return { currentStage: "confirm", subPhase: null };
    case "characters":
      return { currentStage: "generate", subPhase: "char-preview" };
    case "scenes":
      // T22-NEW-5 (2026-05-22): /scenes URL now maps exclusively to scene-refs-preview (R4-3).
      // R4-2 scene-preview has been removed; backend Wave 8 removes scene_review ui_phase.
      return { currentStage: "generate", subPhase: "scene-refs-preview" };
    case "generating":
      // We don't know if it's text-gen or shot-gen from URL alone — default to text-gen
      // and let the polling effect inside StageC promote to shot-gen as backend stage advances.
      return { currentStage: "generate", subPhase: "text-gen" };
    case "preview":
      return { currentStage: "preview", subPhase: "shot-gen" }; // shot-gen so re-entry doesn't trigger text-gen polling
    case "delivery":
      return { currentStage: "deliver", subPhase: "shot-gen" };
  }
}

// RISK-T14-3: Deduped from two identical inline Set definitions
// (POST_CHAR_STAGES_FOR_CHARS inside the "characters" branch and
//  POST_CHAR_STAGES inside the "scenes" branch — values were identical).
// RISK-T15-2 fix: screenplay + storyboard removed from POST_CHAR_STAGES.
// These stages mean "scenes data is still being generated" — NOT "past scenes checkpoint".
// Including them caused reconcile() to boot user from /scenes → /generating permanently,
// because POST_CHAR_STAGES.has(backendStage) returned true and scenesConfirmed was still false.
// POST_CHAR_STAGES should only include stages AFTER scenes have been confirmed by the user.
const POST_CHAR_STAGES = new Set([
  "image_preparation",
  "image_generation",
  "bgm",
  "completed",
]);

/**
 * Wave 9 / DEC-030: Backend `ui_phase` is the new authoritative state machine.
 * When `status.ui_phase` is present, frontend should derive URL directly from it
 * instead of multi-step heuristics on (backendStage + charactersConfirmed + scenesConfirmed).
 *
 * 9-state mapping (T21-NEW-7 v1.4 — 必须与 backend `_derive_ui_phase()` 9 状态同步,
 *   见 `app/api/chapters.py` L67-145 + STATUS_API_CONTRACT v1.4 §2):
 *
 * T22-NEW-5 (2026-05-22): 砍 R4-2 (scene_review) 前端映射已移除.
 *   Backend Wave 8 会同步移除 scene_review ui_phase + pipeline R4-2 wait loop.
 *   部署铁律: Frontend T22-NEW-5 暂不部署, 等 Backend Wave 8 完成后同步上线.
 *
 *   input                    → /create root (no project yet, URL has no [uuid])
 *                              We can't actually navigate to /outline here because we'd lose
 *                              the [uuid] segment — caller handles this by NOT redirecting.
 *                              For reconcile purposes we return "outline".
 *   outline_review           → /outline  (StageB confirm)
 *   char_review_pending      → /generating (Stage 1/2 running, no checkpoint yet)
 *   char_review              → /characters (R4-1: user confirms characters)
 *   scene_review_pending     → /generating (Stage 3 running, between confirm-chars and scenes_ready)
 *   scene_review             → [T22-NEW-5 砍] 前端映射已移除, backend Wave 8 移除此 ui_phase
 *   storyboard_running       → /generating (Stage 4 LLM 或 Stage 4.5 anchor 生成)
 *   scene_references_review  → /scenes (R4-3: T21-NEW-7 用户确认场景参考图视觉, 保留)
 *   shot_generating          → /generating (Stage 5 + image_prep + bgm, "后台生成" allowed here)
 *   completed                → /preview
 */
const UI_PHASE_TO_URL: Record<string, UrlStage> = {
  input: "outline",
  outline_review: "outline",
  char_review_pending: "generating",
  char_review: "characters",
  scene_review_pending: "generating",
  // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene_review ui_phase 映射已移除.
  //   Backend Wave 8 会同步移除 scene_review ui_phase + pipeline R4-2 wait loop.
  //   保留注释提醒: 部署时必须 Frontend + Backend 同步上线.
  storyboard_running: "generating",
  // T21-NEW-7 v1.4 (2026-05-21 DEC-047): Stage 4.5 R4-3 真场景参考图确认.
  // URL 复用 /scenes 段 (与 scene_review 共用), 但渲染不同组件 + hydrate 不同 endpoint.
  scene_references_review: "scenes",
  shot_generating: "generating",
  completed: "preview",
};

/**
 * Decide the "true" UrlStage when URL says one thing but backend reports another.
 * Backend status is authoritative for transient stages; URL is authoritative for
 * post-completion navigation (preview / delivery).
 *
 * Wave 9 / DEC-030: When `uiPhase` is present we trust it as authoritative — this
 * replaces the old multi-branch heuristic (backendStage × charactersConfirmed × scenesConfirmed).
 * The legacy heuristic is kept as a fallback for old backend versions that don't yet
 * emit `ui_phase` (backward-compat, can be removed once backend rollout is verified).
 *
 * B37 logging: every branch logs [createUrl] prefix so DevTools can trace routing decisions.
 * B27 stale-backendStage coverage: POST_CHAR_STAGES set covers all stages past character_ready,
 * so a stale backendStage (e.g. "character_design") that is NOT in the set will correctly
 * NOT override the URL when the URL is "scenes" — that's the intended behavior (stale stage
 * doesn't push user to wrong place). The logging makes this visible.
 */
export function reconcileBackendVsUrl(input: {
  urlStage: UrlStage;
  backendStatus: string | null; // job.status: "pending" | "generating" | "completed" | "failed" | null
  backendStage: string | null; // job.current_stage: "story_generation" | "character_ready" | ...
  uiPhase?: string | null; // Wave 9: backend authoritative 8-state phase machine (preferred when present)
  charactersConfirmed: boolean;
  scenesConfirmed: boolean;
}): UrlStage {
  const { urlStage, backendStatus, backendStage, uiPhase, charactersConfirmed, scenesConfirmed } = input;

  // [createUrl] Log #1 — entry: full input snapshot for every routing decision
  // eslint-disable-next-line no-console
  console.log("[createUrl] reconcileBackendVsUrl input:", {
    urlStage,
    backendStatus,
    backendStage,
    uiPhase,
    charactersConfirmed,
    scenesConfirmed,
  });

  // ============================================================================
  // Wave 9 / DEC-030 PRIMARY PATH: backend ui_phase is authoritative.
  // ============================================================================
  // Backend's `_derive_ui_phase()` already considers:
  //   - chapter.status (job not started → input/outline_review)
  //   - chapter.characters_ready + project.characters_confirmed (char_review vs char_review_pending)
  //   - chapter.scenes_json + project.scenes_confirmed (scene_review vs scene_review_pending)
  //   - chapter.storyboard_ready (storyboard_running vs shot_generating)
  //   - chapter.status === "completed" (completed)
  // So if uiPhase is present we directly map it to URL — no heuristics needed.
  //
  // Special override: URL=delivery is user-initiated post-completion and should be respected.
  if (uiPhase) {
    if (uiPhase === "completed" && urlStage === "delivery") {
      // eslint-disable-next-line no-console
      console.log("[createUrl] Wave9: uiPhase=completed but URL=delivery → keep delivery");
      return "delivery";
    }
    const derived = UI_PHASE_TO_URL[uiPhase];
    if (derived) {
      // eslint-disable-next-line no-console
      console.log("[createUrl] Wave9: derived from uiPhase=", uiPhase, "→ result:", derived);
      return derived;
    }
    // Unknown ui_phase value — log and fall through to legacy heuristic
    // eslint-disable-next-line no-console
    console.warn("[createUrl] Wave9: unknown uiPhase value:", uiPhase, "— falling through to legacy heuristic");
  }
  // ============================================================================
  // LEGACY FALLBACK PATH: pre-Wave-9 backend (no ui_phase field).
  // ============================================================================

  // Backend completed → force preview (unless user already in delivery)
  if (backendStatus === "completed" || backendStage === "completed") {
    const result = urlStage === "delivery" ? "delivery" : "preview";
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: backend completed → result:", result);
    return result;
  }

  // Backend failed → keep user where they are (StageC handles error UI)
  if (backendStatus === "failed") {
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: backend failed → result: generating");
    return "generating";
  }

  // Backend has no job yet (pending) → user must confirm outline first
  if (!backendStatus || backendStatus === "pending") {
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: backend pending/null → result: outline (urlStage was:", urlStage, ")");
    return "outline";
  }

  // Backend is mid-pipeline ("generating")
  // Pipeline stages map roughly to:
  //   story_generation, character_design        → generating (early)
  //   character_ready                            → characters (sub-phase char-preview)
  //   screenplay, storyboard                     → generating (mid LLM, user already past char/scene preview)
  //   image_preparation, image_generation, bgm   → generating (late, after scenes confirmed)
  if (backendStage === "character_ready") {
    // Backend just finished Stage 2; if user has already confirmed characters, they're in scenes / generating
    let result: UrlStage;
    if (!charactersConfirmed && urlStage === "characters") {
      result = "characters";
    } else if (!charactersConfirmed) {
      result = "characters"; // force user to char checkpoint
    } else if (!scenesConfirmed && urlStage === "scenes") {
      result = "scenes";
    } else {
      result = "generating";
    }
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: character_ready → result:", result, "(charactersConfirmed:", charactersConfirmed, "scenesConfirmed:", scenesConfirmed, ")");
    return result;
  }

  // For all other backend stages (story_generation, character_design, screenplay,
  // storyboard, image_preparation, image_generation, bgm) we trust URL if it's a
  // legal "generating" or sub-phase value, else default to /generating.
  //
  // BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 defensive guard:
  //   Only bounce /characters → /generating when backend has DEFINITELY moved past
  //   character_ready (i.e. backendStage is in POST_CHAR_STAGES). If backend is at
  //   character_ready / null / story_generation / character_design, allow /characters
  //   so the user can see the checkpoint even if heuristic says charactersConfirmed=true.
  if (urlStage === "characters") {
    const backendPastCharStage = backendStage ? POST_CHAR_STAGES.has(backendStage) : false;
    // Bounce ONLY when both: (1) backend has truly advanced past character_ready, AND
    // (2) characters are already confirmed. Otherwise let user see /characters.
    const result = (charactersConfirmed && backendPastCharStage) ? "generating" : "characters";
    // eslint-disable-next-line no-console
    console.log(
      "[createUrl] branch: urlStage=characters, charactersConfirmed=",
      charactersConfirmed,
      "backendPastCharStage=",
      backendPastCharStage,
      "→ result:",
      result
    );
    return result;
  }

  // B27 fix: /scenes URL should only show scene-preview when backend is at character_ready.
  // If backend has advanced past character_ready into screenplay/storyboard/image_* stages,
  // scene-preview is no longer meaningful — redirect to /generating (progress bar).
  // This handles the case where user refreshes at /scenes while backend is mid-Stage-3.
  // B27 stale note: if backendStage is stale (e.g. still "character_design" due to failed hydrate),
  // it will NOT be in POST_CHAR_STAGES, so we fall through to "return scenes" — which is the
  // safest default (show the checkpoint rather than jumping somewhere unexpected).
  if (urlStage === "scenes") {
    if (scenesConfirmed) {
      // eslint-disable-next-line no-console
      console.log("[createUrl] branch: urlStage=scenes, scenesConfirmed=true → result: generating");
      return "generating";
    }
    // If backend is past character_ready, scenes checkpoint is no longer actionable
    if (backendStage && POST_CHAR_STAGES.has(backendStage)) {
      // eslint-disable-next-line no-console
      console.log("[createUrl] branch: urlStage=scenes, backendStage=", backendStage, "is in POST_CHAR_STAGES → result: generating");
      return "generating";
    }
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: urlStage=scenes, backendStage=", backendStage, "not in POST_CHAR_STAGES (stale or character_ready) → result: scenes");
    return "scenes";
  }
  if (urlStage === "generating") {
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: urlStage=generating → result: generating");
    return "generating";
  }
  if (urlStage === "outline") {
    // Outline already confirmed (since we're in "generating" status). Send to /generating.
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: urlStage=outline but status=generating → result: generating");
    return "generating";
  }
  if (urlStage === "preview" || urlStage === "delivery") {
    // Preview before pipeline finished — send to /generating
    // eslint-disable-next-line no-console
    console.log("[createUrl] branch: urlStage=", urlStage, "before completion → result: generating");
    return "generating";
  }
  // eslint-disable-next-line no-console
  console.log("[createUrl] branch: default fallthrough → result: generating");
  return "generating";
}

/**
 * Build the canonical URL for the current state.
 * Returns null if the state has no project yet (Stage A).
 */
export function buildCreateUrl(projectUuid: string | null, stage: UrlStage | null): string | null {
  if (!projectUuid || !stage) return null;
  return `/create/${projectUuid}/${stage}`;
}
