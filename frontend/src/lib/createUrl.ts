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
      if (subPhase === "scene-preview") return "scenes";
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
      return { currentStage: "generate", subPhase: "scene-preview" };
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

/**
 * Decide the "true" UrlStage when URL says one thing but backend reports another.
 * Backend status is authoritative for transient stages; URL is authoritative for
 * post-completion navigation (preview / delivery).
 */
export function reconcileBackendVsUrl(input: {
  urlStage: UrlStage;
  backendStatus: string | null; // job.status: "pending" | "generating" | "completed" | "failed" | null
  backendStage: string | null; // job.current_stage: "story_generation" | "character_ready" | ...
  charactersConfirmed: boolean;
  scenesConfirmed: boolean;
}): UrlStage {
  const { urlStage, backendStatus, backendStage, charactersConfirmed, scenesConfirmed } = input;

  // Backend completed → force preview (unless user already in delivery)
  if (backendStatus === "completed" || backendStage === "completed") {
    if (urlStage === "delivery") return "delivery";
    return "preview";
  }

  // Backend failed → keep user where they are (StageC handles error UI)
  if (backendStatus === "failed") {
    return "generating";
  }

  // Backend has no job yet (pending) → user must confirm outline first
  if (!backendStatus || backendStatus === "pending") {
    if (urlStage === "outline") return "outline";
    return "outline"; // anything else is invalid pre-confirm
  }

  // Backend is mid-pipeline ("generating")
  // Pipeline stages map roughly to:
  //   story_generation, character_design        → generating (early)
  //   character_ready                            → characters (sub-phase char-preview)
  //   screenplay, storyboard                     → generating (mid LLM, user already past char/scene preview)
  //   image_preparation, image_generation, bgm   → generating (late, after scenes confirmed)
  if (backendStage === "character_ready") {
    // Backend just finished Stage 2; if user has already confirmed characters, they're in scenes / generating
    if (!charactersConfirmed && urlStage === "characters") return "characters";
    if (!charactersConfirmed) return "characters"; // force user to char checkpoint
    if (!scenesConfirmed && urlStage === "scenes") return "scenes";
    return "generating";
  }

  // For all other backend stages (story_generation, character_design, screenplay,
  // storyboard, image_preparation, image_generation, bgm) we trust URL if it's a
  // legal "generating" or sub-phase value, else default to /generating.
  if (urlStage === "characters") {
    if (charactersConfirmed) return "generating";
    return "characters";
  }
  if (urlStage === "scenes") {
    if (scenesConfirmed) return "generating";
    return "scenes";
  }
  if (urlStage === "generating") return "generating";
  if (urlStage === "outline") {
    // Outline already confirmed (since we're in "generating" status). Send to /generating.
    return "generating";
  }
  if (urlStage === "preview" || urlStage === "delivery") {
    // Preview before pipeline finished — send to /generating
    return "generating";
  }
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
