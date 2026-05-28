"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, AlertCircle, Loader2, Palette } from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken, fetchBgmInfo } from "@/lib/api";
import { mockOutline } from "@/lib/mock-data";
import type {
  StoryOutline,
  StoryLength,
  Shot,
  SafetyAdvice,
  PreviewCharacter,
  PreviewScene,
  AspectRatio,
} from "@/types/create";
import { MOOD_OPTIONS } from "@/types/create";
import {
  buildCreateUrl,
  deriveUrlStageFromState,
  isUrlStage,
  reconcileBackendVsUrl,
  stateFromUrlStage,
  type UrlStage,
} from "@/lib/createUrl";
import { toAbsoluteUrl } from "@/lib/url";
import CreateHeader from "@/components/layout/CreateHeader";
import StoryIdeaInput from "@/components/ui/StoryIdeaInput";
import LengthSelector from "@/components/ui/LengthSelector";
import StyleSelector from "@/components/ui/StyleSelector";
import AspectRatioSelector from "@/components/ui/AspectRatioSelector";
import CharacterUploader from "@/components/ui/CharacterUploader";
import SceneUploader from "@/components/ui/SceneUploader";
import StageB from "@/components/create/StageB";
import StageC from "@/components/create/StageC";
import StageD from "@/components/create/StageD";
import StageE from "@/components/create/StageE";

// Length → API parameters mapping
const LENGTH_PARAMS: Record<StoryLength, { duration: number; characters: number }> = {
  flash: { duration: 1, characters: 2 },
  short: { duration: 3, characters: 3 },
  medium: { duration: 6, characters: 3 },
  epic: { duration: 6, characters: 4 },
};

const OUTLINE_STAGES = [
  { time: 0, progress: 5, text: "正在创建项目...", sub: "初始化故事参数" },
  { time: 5, progress: 15, text: "正在分析你的故事创意...", sub: "理解故事方向和情感" },
  { time: 15, progress: 35, text: "正在设计角色和场景...", sub: "Claude 正在为你的故事构思完整大纲" },
  { time: 35, progress: 60, text: "正在构思情节走向...", sub: "设计起承转合和关键冲突" },
  { time: 55, progress: 80, text: "正在打磨故事大纲...", sub: "优化角色弧线和情感节奏" },
  { time: 75, progress: 90, text: "即将完成，请稍候...", sub: "最终整理输出" },
];

function StageA() {
  const { state, dispatch } = useCreate();
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const [ideaError, setIdeaError] = useState("");
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [generatingOutline, setGeneratingOutline] = useState(false);
  const [outlineProgress, setOutlineProgress] = useState(0);
  const [outlineStageIdx, setOutlineStageIdx] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimers = useCallback(() => {
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    if (progressRef.current) { clearInterval(progressRef.current); progressRef.current = null; }
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  // Progress timer during outline generation
  useEffect(() => {
    if (!generatingOutline) return;
    const startTime = Date.now();
    progressRef.current = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setElapsedTime(Math.floor(elapsed));
      // Find current stage
      let idx = 0;
      for (let i = OUTLINE_STAGES.length - 1; i >= 0; i--) {
        if (elapsed >= OUTLINE_STAGES[i].time) { idx = i; break; }
      }
      setOutlineStageIdx(idx);
      // Smooth progress interpolation
      const stage = OUTLINE_STAGES[idx];
      const nextStage = OUTLINE_STAGES[idx + 1];
      if (nextStage) {
        const stageElapsed = elapsed - stage.time;
        const stageDuration = nextStage.time - stage.time;
        const fraction = Math.min(stageElapsed / stageDuration, 1);
        setOutlineProgress(stage.progress + (nextStage.progress - stage.progress) * fraction);
      } else {
        setOutlineProgress(stage.progress);
      }
    }, 200);
    return () => { if (progressRef.current) clearInterval(progressRef.current); };
  }, [generatingOutline]);

  const handleSubmit = async () => {
    if (!state.idea.trim() && !state.documentText?.trim()) {
      setIdeaError("请输入故事创意或上传故事文档");
      return;
    }
    if (state.idea.length > 500) {
      setIdeaError("故事创意不能超过 500 字");
      return;
    }
    setIdeaError("");
    setApiError("");
    setLoading(true);
    setGeneratingOutline(true);
    setOutlineProgress(0);
    setOutlineStageIdx(0);
    setElapsedTime(0);

    const token = getStoredToken();

    // If not logged in or no token, use mock data
    if (!isLoggedIn || !token) {
      timerRef.current = setTimeout(() => {
        setOutlineProgress(100);
        setTimeout(() => {
          dispatch({ type: "SET_OUTLINE", payload: mockOutline });
          dispatch({ type: "SET_STAGE", payload: "confirm" });
          setLoading(false);
          setGeneratingOutline(false);
        }, 500);
      }, 3000);
      return;
    }

    try {
      const params = LENGTH_PARAMS[state.length] || LENGTH_PARAMS.short;

      // Step 1: Create project
      const project = await apiFetch<{ project_id: string }>(
        "/projects/",
        {
          method: "POST",
          body: JSON.stringify({
            original_idea: state.idea.trim(),
            style_preset: state.stylePreset || "illustration",
            total_chapters: 1,
            chapter_duration_minutes: params.duration,
            character_count: params.characters,
            language: "zh-CN",
            aspect_ratio: state.aspectRatio || "2:3",
            // B33: pass user-selected mood to backend (null = let LLM auto-infer)
            user_selected_mood: state.userSelectedMood || null,
            document_text: state.documentText || null,
            custom_style_analysis: state.customStyleAnalysis || null,
            character_refs_analysis: state.characters
              .filter(c => c.analysisResult)
              .map(c => c.analysisResult),
            scene_refs_analysis: state.scenes
              .filter(s => s.analysisResult)
              .map(s => s.analysisResult),
          }),
        },
        token
      );

      // Save projectId for StageB to use
      dispatch({ type: "SET_PROJECT_ID", payload: project.project_id });

      // Step 2: Generate outline (synchronous, 10-30s)
      const outline = await apiFetch<StoryOutline>(
        `/projects/${project.project_id}/generate-outline`,
        { method: "POST" },
        token
      );

      // Success: jump to 100% then transition
      setOutlineProgress(100);
      await new Promise((r) => setTimeout(r, 500));
      dispatch({ type: "SET_OUTLINE", payload: outline });
      dispatch({ type: "SET_STAGE", payload: "confirm" });
      // UX-16: Navigate to dynamic route so URL reflects state. Use replace so
      // back button doesn't return to the form (which would re-create the project).
      router.replace(`/create/${project.project_id}/outline`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "生成失败，请稍后重试";
      setApiError(message);
    } finally {
      setLoading(false);
      setGeneratingOutline(false);
    }
  };

  const handleIdeaChange = (value: string) => {
    dispatch({ type: "SET_IDEA", payload: value });
    if (ideaError) setIdeaError("");
  };

  // ============ Outline Generation Progress View ============
  if (generatingOutline) {
    const currentStage = OUTLINE_STAGES[outlineStageIdx];
    return (
      <main className="container-lg py-8 pb-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-lg mx-auto text-center"
        >
          {/* Error state */}
          {apiError ? (
            <>
              <AlertCircle className="w-16 h-16 text-error mx-auto mb-6" />
              <h1 className="text-2xl font-bold mb-2">生成遇到问题</h1>
              <p className="text-text-tertiary text-sm mb-4">{apiError}</p>
              <button
                onClick={() => { setGeneratingOutline(false); setLoading(false); setApiError(""); }}
                className="btn-primary px-8"
              >
                返回重试
              </button>
            </>
          ) : (
            <>
              {/* Animated icon */}
              <motion.div
                className="mb-8"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                <Loader2 className="w-16 h-16 text-brand-primary mx-auto animate-spin" />
              </motion.div>

              {/* Stage text */}
              <motion.h1
                key={currentStage.text}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-xl font-bold mb-2"
              >
                {currentStage.text}
              </motion.h1>
              <p className="text-text-tertiary text-sm mb-8">{currentStage.sub}</p>

              {/* Progress bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-text-muted">进度</span>
                  <span className="text-xs text-text-muted">{Math.round(outlineProgress)}%</span>
                </div>
                <div className="w-full h-2 bg-bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-brand-primary to-purple-500 rounded-full"
                    animate={{ width: `${outlineProgress}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
              </div>

              {/* Elapsed time */}
              <p className="text-xs text-text-muted">
                已等待 {elapsedTime} 秒
              </p>
            </>
          )}
        </motion.div>
      </main>
    );
  }

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">开始创作</h1>
          <p className="text-text-tertiary text-sm">
            输入创意，AI 帮你生成完整条漫
          </p>
        </div>

        {/* Form */}
        <div className="space-y-8">
          {/* Story Idea + Document Upload */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <StoryIdeaInput
              value={state.idea}
              onChange={handleIdeaChange}
              error={ideaError}
              documentFile={state.documentFile}
              onDocumentUpload={(file, text) =>
                dispatch({ type: "SET_DOCUMENT", payload: { file, text } })
              }
            />
          </motion.div>

          {/* Length Selector */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <LengthSelector
              value={state.length}
              onChange={(v) => dispatch({ type: "SET_LENGTH", payload: v })}
              continuationMode={state.continuationMode}
              onContinuationModeChange={(m) =>
                dispatch({ type: "SET_CONTINUATION_MODE", payload: m })
              }
            />
          </motion.div>

          {/* Aspect Ratio */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <AspectRatioSelector
              value={state.aspectRatio}
              onChange={(v) => dispatch({ type: "SET_ASPECT_RATIO", payload: v })}
            />
          </motion.div>

          {/* B33: Mood Selector — moved here from StageB so user sets mood before outline generation */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.225 }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Palette className="w-4 h-4 text-brand-primary" />
              <h2 className="text-sm font-medium text-text-secondary">
                情绪基调
                <span className="text-text-muted font-normal ml-1">（可选，AI 会自动推断）</span>
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {MOOD_OPTIONS.map((mood) => (
                <button
                  key={mood}
                  type="button"
                  onClick={() =>
                    dispatch({
                      type: "SET_USER_SELECTED_MOOD",
                      payload: state.userSelectedMood === mood ? null : mood,
                    })
                  }
                  className={`px-3 py-1.5 rounded-full text-xs border transition-all ${
                    state.userSelectedMood === mood
                      ? "border-brand-primary/50 bg-brand-primary/10 text-brand-primary"
                      : "border-white/10 text-text-muted hover:border-white/20"
                  }`}
                >
                  {mood}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Style Selector */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <StyleSelector
              value={state.stylePreset}
              onChange={(v) => dispatch({ type: "SET_STYLE_PRESET", payload: v })}
              customStyleImage={state.customStyleImage}
              customStyleImageUrl={state.customStyleImageUrl}
              customStyleKeywords={state.customStyleKeywords}
              onCustomStyleChange={(image, imageUrl, keywords, analysis) =>
                dispatch({ type: "SET_CUSTOM_STYLE", payload: { image, imageUrl, keywords, analysis } })
              }
            />
          </motion.div>

          {/* Character & Scene Uploaders */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-6"
          >
            <CharacterUploader
              characters={state.characters}
              storyLength={state.length}
              onAdd={(c) => dispatch({ type: "ADD_CHARACTER", payload: c })}
              onRemove={(id) => dispatch({ type: "REMOVE_CHARACTER", payload: id })}
            />
            <SceneUploader
              scenes={state.scenes}
              storyLength={state.length}
              onAdd={(s) => dispatch({ type: "ADD_SCENE", payload: s })}
              onRemove={(id) => dispatch({ type: "REMOVE_SCENE", payload: id })}
            />
          </motion.div>

          {/* Submit */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="pt-2"
          >
            {/* API Error */}
            {apiError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-error/10 border border-error/20 mb-3">
                <AlertCircle className="w-4 h-4 text-error flex-shrink-0" />
                <span className="text-sm text-error flex-1">{apiError}</span>
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 py-3.5 text-base"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  AI 正在构思故事大纲...
                </>
              ) : apiError ? (
                <>
                  <Sparkles className="w-4 h-4" />
                  重试
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  生成故事
                </>
              )}
            </button>
            <p className="text-center text-text-muted text-xs mt-3">
              {loading ? "大纲生成中，约需 10-30 秒..." : "AI 将根据你的创意生成完整故事大纲"}
            </p>
          </motion.div>
        </div>
      </motion.div>
    </main>
  );
}

// ============ UX-16: State hydration + URL sync ============

/**
 * Wave 9 / DEC-030: Backend status response shape (single source of truth).
 * The 6 new fields (ui_phase, hydrate_hints, characters_confirmed, scenes_confirmed,
 * storyboard_ready, outline_ready) are emitted by post-Wave-9 backend. All optional
 * so old backend deployments still type-check.
 *
 * Contract source: `.claude/agents/backend-progress/context-for-others.md` (top section)
 *   + `app/schemas/chapter.py` (HydrateHints + ChapterStatus models).
 */
interface HydrateHints {
  endpoint: string; // e.g. "/api/projects/{project_id}/chapters/1/storyboard"
  display_field: string; // e.g. "shots" | "scenes" | "characters"
  expected_data_shape: string; // e.g. "list[Shot]"
}

interface ChapterStatusResp {
  status: string;
  stage: string | null;
  progress: number;
  message: string;
  estimated_remaining_seconds?: number | null;
  actual_elapsed_sec?: number | null;  // RISK-NEW-1: job已运行秒数，供 useETA sanity check 用
  // Wave 9 / DEC-030 — new authoritative fields (optional for backward compat)
  // T21-NEW-7 (2026-05-21 DEC-047 v1.4): 9 状态机 (加 scene_references_review)
  ui_phase?:
    | "input"
    | "outline_review"
    | "char_review_pending"
    | "char_review"
    | "scene_review_pending"
    | "scene_review"
    | "storyboard_running"
    | "scene_references_review"  // T21-NEW-7 v1.4: Stage 4.5 R4-3 等用户确认场景参考图
    | "shot_generating"
    | "completed"
    | null;
  hydrate_hints?: HydrateHints | null;
  characters_confirmed?: boolean;
  scenes_confirmed?: boolean;
  storyboard_ready?: boolean;
  outline_ready?: boolean;
  // T21-NEW-7 v1.4: scene_references R4-3 字段 (STATUS_API_CONTRACT v1.4 §1.2)
  scene_references_ready?: boolean;       // chapter.scene_references_json 非空 → Stage 4.5 完成
  scene_references_confirmed?: boolean;   // project.scene_references_confirmed → R4-3 已确认
  failed_shot_count?: number;
  partial_failure?: boolean;
}

interface ProjectDetailResp {
  id: string;
  title: string;
  original_idea: string;
  style_preset: string;
  aspect_ratio: string | null;
  // B33: user_selected_mood persisted at project creation
  user_selected_mood?: string | null;
  // B49: backend DB field exposed by GET /projects/{uuid} — true once user clicked "确认角色，继续"
  characters_confirmed?: boolean;
  // B58: backend DB field — true once user clicked "确认场景，继续"
  scenes_confirmed?: boolean;
  created_at: string;
  confirmed_outline?: {
    title?: string;
    title_en?: string;
    summary?: string;
    mood?: string;
    user_selected_mood?: string | null;
    plot_points?: Array<{ description?: string; content?: string }>;
    // B36 v3: backend stores raw Stage 1 JSON which has characters_overview (not characters).
    // Both fields are declared here so the compiler allows reading either.
    characters?: Array<{
      id?: string;
      name?: string;
      name_en?: string;
      description?: string;
      personality?: string;
      portrait_url?: string | null;
    }>;
    characters_overview?: Array<{
      id?: string;
      name?: string;
      name_suggestion?: string;   // Stage 1 LLM outputs name_suggestion, not name
      name_en?: string;
      description?: string;
      personality?: string;
      portrait_url?: string | null;
    }>;
    scenes?: Array<{ id?: string; name?: string; description?: string; description_zh?: string; location_type?: string }>;
    endings?: Array<{ id?: string; description?: string; isSelected?: boolean }>;
    // B42 fix: backend confirmed_outline_json uses "ending_options" (not "endings").
    // Both are declared so the compiler allows reading either field.
    ending_options?: Array<{ id?: string; description?: string; isSelected?: boolean }>;
  } | null;
}

interface ChapterStoryResp {
  characters?: Array<{ id?: string; name: string; description?: string; portrait_url?: string | null }>;
  // B42 / Wave 10 / RISK-T16-4: Stage 3 ScreenplayWriter stores scenes_json with the full LLM payload.
  // action_beats is critical — StoryboardDirector (Stage 4) reads it to generate shots.
  // We preserve ALL fields here so they can flow through to confirm-scenes POST intact.
  scenes?: Array<{
    id?: string;
    name?: string;
    description?: string;
    description_zh?: string;
    scene_id?: number;
    scene_heading?: string;
    plot_point?: string;
    location_id?: string;
    time_of_day?: string;
    weather?: string;
    lighting_condition?: string;
    atmosphere?: string | { mood?: string };
    action_beats?: unknown[];
    narration?: string;
    characters_in_scene?: string[];
    visual_description?: string;
    [key: string]: unknown;
  }>;
}

interface StoryboardResp {
  storyboard: unknown;
  chapter_number: number;
  project_id: string;
}

/**
 * D.21: Wrap a promise with a timeout. If the promise doesn't resolve within
 * `ms` milliseconds, resolves with `fallback` instead (never rejects).
 * Used to bound hydrate API calls when backend is slow (e.g. DB connection lag).
 */
function withTimeout<T>(promise: Promise<T>, ms: number, fallback: T): Promise<T> {
  const timer = new Promise<T>((resolve) => setTimeout(() => resolve(fallback), ms));
  return Promise.race([promise, timer]);
}

/**
 * UX-16: Pull all backend data and dispatch a HYDRATE_FROM_BACKEND action so
 * the rest of the app behaves exactly like it just walked the user through
 * Stages A-D in this session.
 *
 * Returns the reconciled UrlStage we should redirect to.
 */
// Payload shape for HYDRATE_FROM_BACKEND — see CreateAction in types/create.ts
type HydratePayload = Extract<
  import("@/types/create").CreateAction,
  { type: "HYDRATE_FROM_BACKEND" }
>["payload"];

async function hydrateProjectFromBackend(
  projectUuid: string,
  token: string,
  urlStage: UrlStage
): Promise<{
  hydratePayload: HydratePayload | null;
  reconciledStage: UrlStage;
  notFound: boolean;
}> {
  // ── Step 1: Fetch project — this is the ONLY fetch that should set notFound=true ──
  // B28 fix: Stage 3 LLM (ScreenplayWriter) can block backend for up to 254s.
  // During that period GET /projects is slow but eventually returns.
  // Old 30s timeout was too aggressive — it aborted valid hydrations mid-pipeline.
  // New timeout: 120s (2 min). If still blocked beyond that, we retry once silently
  // rather than showing the misleading "加载项目失败" error to the user.
  const PROJECT_FETCH_TIMEOUT_MS = 120000;
  let project: ProjectDetailResp;
  try {
    const _projectFetchStart = Date.now();
    // [hydrate] Log #1 — project fetch start with timeout config
    // eslint-disable-next-line no-console
    console.log("[hydrate] project fetch start, projectUuid=", projectUuid, "timeout=", PROJECT_FETCH_TIMEOUT_MS, "ms");
    const projectOrTimeout = await withTimeout<ProjectDetailResp | null>(
      apiFetch<ProjectDetailResp>(`/projects/${projectUuid}`, {}, token),
      PROJECT_FETCH_TIMEOUT_MS,
      null
    );
    // [hydrate] Log #2 — project fetch result (OK vs TIMEOUT)
    // eslint-disable-next-line no-console
    console.log("[hydrate] project fetch result after", Date.now() - _projectFetchStart, "ms:", projectOrTimeout ? "OK (id=" + (projectOrTimeout as ProjectDetailResp).id + ")" : "TIMEOUT/NULL");
    if (!projectOrTimeout) {
      console.warn("[hydrate] project fetch timed out after", PROJECT_FETCH_TIMEOUT_MS, "ms");
      return { hydratePayload: null, reconciledStage: urlStage, notFound: false };
    }
    project = projectOrTimeout;
  } catch (err) {
    // Project truly doesn't exist (404) or auth failed (401) → surface as notFound/error
    const msg = err instanceof Error ? err.message : String(err);
    const isNotFound = /404|不存在|not found/i.test(msg);
    // [hydrate] Log #3 — project fetch threw
    // eslint-disable-next-line no-console
    console.error("[hydrate] project fetch threw:", msg, "isNotFound=", isNotFound);
    console.warn("[hydrate] project fetch failed:", msg);
    return { hydratePayload: null, reconciledStage: urlStage, notFound: isNotFound };
  }

  try {
    // ── Step 2: Fetch chapter data — 404/400 here is ROUTINE (pre-confirm-outline or mid-pipeline) ──
    // status: 404 before chapter created → default to "pending"
    // storyboard/story: 404 before generation, 400 mid-pipeline → null (handled downstream)
    // B28 fix: same rationale as PROJECT_FETCH_TIMEOUT_MS — Stage 3 can block DB reads for 254s.
    // Raise chapter fetch timeout to 90s (less than project fetch since these can fall back to defaults).
    const HYDRATE_CHAPTER_TIMEOUT_MS = 90000;
    const defaultStatus: ChapterStatusResp = { status: "pending", stage: null, progress: 0, message: "" };
    // BUG-T13-PREVIEW-DIRECT-LOAD-SLOW: parallelize ALL chapter+BGM fetches in one Promise.all
    // batch (was: chapter fetches in Promise.all, then BGM serially after — adds latency on direct
    // /preview URL load). All four fetches independent; running concurrently shaves seconds on
    // the critical path when user opens /preview directly (vs from dashboard).
    // [hydrate] Log #4 — chapter+BGM fetches start
    // eslint-disable-next-line no-console
    console.log("[hydrate] chapter+BGM fetch start — 4 parallel, timeout=", HYDRATE_CHAPTER_TIMEOUT_MS, "ms");
    const _chapterFetchStart = Date.now();
    const [status, storyboardData, storyData, bgmInfo] = await Promise.all([
      withTimeout(
        // RISK-T20-11.v2 (Wave 4): silentStatuses=[404] — chapter doesn't exist until
        // confirm-outline. /outline phase hydrate triggers 1 by-design 404, no need to warn.
        apiFetch<ChapterStatusResp>(`/projects/${projectUuid}/chapters/1/status`, {}, token, { silentStatuses: [404] }).catch(
          (e) => {
            // eslint-disable-next-line no-console
            console.warn("[hydrate] chapter status 404/error (routine pre-confirm):", e instanceof Error ? e.message : e);
            return defaultStatus;
          }
        ),
        HYDRATE_CHAPTER_TIMEOUT_MS,
        defaultStatus
      ),
      withTimeout(
        apiFetch<StoryboardResp>(`/projects/${projectUuid}/chapters/1/storyboard`, {}, token, { silentStatuses: [400, 404] }).catch(
          (e) => {
            // eslint-disable-next-line no-console
            console.warn("[hydrate] storyboard 404/error (routine pre-generation):", e instanceof Error ? e.message : e);
            return null;
          }
        ),
        HYDRATE_CHAPTER_TIMEOUT_MS,
        null as StoryboardResp | null
      ),
      withTimeout(
        apiFetch<ChapterStoryResp>(`/projects/${projectUuid}/chapters/1/story`, {}, token, { silentStatuses: [400, 404] }).catch(
          (e) => {
            // D.21: 400 = chapter in pending/generating_story state (has characters_json but not full_script yet)
            // 404 = chapter not yet created. Both are routine pre-story-complete.
            // eslint-disable-next-line no-console
            console.warn("[hydrate] chapter story 400/404/error (routine pre-story-ready):", e instanceof Error ? e.message : e);
            return null;
          }
        ),
        HYDRATE_CHAPTER_TIMEOUT_MS,
        null as ChapterStoryResp | null
      ),
      // BUG-T13-PREVIEW-DIRECT-LOAD-SLOW: bgm fetch in parallel with chapter fetches
      // (was: serialized AFTER chapter fetches). 15s timeout same as before — best-effort only.
      // RISK-T20-11.v2 (Wave 4): pass silentStatuses=[404] so pre-BGM-generation 404 doesn't
      // warn (BGM is only generated at end of Stage 6, so /outline/characters/scenes phases
      // all 404 by design).
      withTimeout(
        fetchBgmInfo(projectUuid, 1, token, { silentStatuses: [404] }).catch((e) => {
          // eslint-disable-next-line no-console
          console.warn("[hydrate] bgm 404/error (routine pre-bgm-generation):", e instanceof Error ? e.message : e);
          return null;
        }),
        15000,
        null as Awaited<ReturnType<typeof fetchBgmInfo>> | null
      ),
    ]);
    // [hydrate] Log #5 — chapter fetches complete: what did we get?
    // eslint-disable-next-line no-console
    console.log("[hydrate] chapter+BGM fetches done after", Date.now() - _chapterFetchStart, "ms — status:", status.status, "stage:", status.stage, "progress:", status.progress, "| storyboard:", storyboardData ? "OK" : "null", "| story chars:", storyData?.characters?.length ?? "null", "| bgm:", bgmInfo ? "OK" : "null");

    // Reconcile URL vs backend BEFORE we know charactersConfirmed/scenesConfirmed
    // (we'll infer them from backend stage progression below).
    // Heuristic: if backend stage is past "character_ready", characters are confirmed.
    // If backend stage is past "screenplay", scenes are confirmed.
    const ADVANCED_STAGES = new Set([
      "screenplay",
      "storyboard",
      "image_preparation",
      "image_generation",
      "bgm",
      "completed",
    ]);
    // Wave 9 / DEC-030: Prefer `status.characters_confirmed` (post-Wave-9 backend, real-time
    // from latest DB read inside the status endpoint). Fall back to `project.characters_confirmed`
    // (B49 — cached at GET /projects request start) and finally to ADVANCED_STAGES heuristic.
    const charactersConfirmed =
      status.characters_confirmed === true ||         // Wave 9: status response authoritative (newest)
      project.characters_confirmed === true ||        // B49: ProjectDetail field
      ADVANCED_STAGES.has(status.stage || "") ||
      status.status === "completed";
    // Wave 9 / DEC-030: same precedence for scenes_confirmed.
    const scenesConfirmed =
      status.scenes_confirmed === true ||             // Wave 9: status response authoritative
      project.scenes_confirmed === true ||            // B58: ProjectDetail field
      ADVANCED_STAGES.has(status.stage || "") ||
      status.status === "completed";
    // [B58] trace: log the actual value of project.scenes_confirmed from backend
    // eslint-disable-next-line no-console
    console.log("[B58] project.scenes_confirmed=", project.scenes_confirmed, "status.scenes_confirmed=", status.scenes_confirmed, "→ scenesConfirmed=", scenesConfirmed, "backendStage=", status.stage);

    // [B49] trace: log the actual value of project.characters_confirmed from backend
    // eslint-disable-next-line no-console
    console.log("[B49] project.characters_confirmed=", project.characters_confirmed, "status.characters_confirmed=", status.characters_confirmed, "→ charactersConfirmed=", charactersConfirmed, "backendStage=", status.stage);

    // Wave 9 / DEC-030: surface hydrate_hints in console for future enhancement +
    // tester / DevTools verify of the new contract surface. Currently the parallel
    // fetch (storyboard + story + bgm) covers all phases, so we don't switch endpoint
    // dynamically — but hints are typed and logged so any future single-endpoint
    // hydrate refactor can read them.
    if (status.hydrate_hints) {
      // eslint-disable-next-line no-console
      console.log(
        "[hydrate] Wave9: status.hydrate_hints.endpoint=",
        status.hydrate_hints.endpoint,
        "display_field=",
        status.hydrate_hints.display_field,
        "expected_shape=",
        status.hydrate_hints.expected_data_shape,
        "(current parallel fetches already cover this — hint logged for verification)",
      );
    }

    const reconciledStage = reconcileBackendVsUrl({
      urlStage,
      backendStatus: status.status,
      backendStage: status.stage,
      uiPhase: status.ui_phase ?? null,               // Wave 9 / DEC-030: backend authoritative
      charactersConfirmed,
      scenesConfirmed,
    });
    // [Router] Log #6 — reconcile decision: URL → decided URL + reason
    // eslint-disable-next-line no-console
    console.log("[Router] reconcile decision:", {
      urlStage,
      backendStatus: status.status,
      backendStage: status.stage,
      progress: status.progress,
      charactersConfirmed,
      scenesConfirmed,
      reconciledStage,
      currentUrl: typeof window !== "undefined" ? window.location.pathname : "(ssr)",
      reason: reconciledStage !== urlStage ? `URL "${urlStage}" overridden by backend → "${reconciledStage}"` : `URL "${urlStage}" matches backend`,
    });

    // Build outline from confirmed_outline (or null if user hasn't confirmed yet)
    const co = project.confirmed_outline;
    let outline: StoryOutline | null = null;
    if (co) {
      outline = {
        title: co.title || project.title || "",
        titleEn: co.title_en || "",
        summary: co.summary || "",
        // B36 v3: backend confirmed_outline_json stores raw Stage 1 output which has
        // characters_overview[*].name_suggestion (not .name). When co.characters is absent
        // (or empty), fall back to co.characters_overview and map name_suggestion → name.
        // portrait_url is always null here; D.21 buildStaticPortraitUrl() will fill it in.
        characters: (() => {
          const rawChars = (co.characters && co.characters.length > 0)
            ? co.characters
            : (co.characters_overview || []);
          // eslint-disable-next-line no-console
          console.log("[B36][hydrate] characters source:", (co.characters && co.characters.length > 0) ? "co.characters" : "co.characters_overview", "count=", rawChars.length);
          return rawChars.map((c, i) => ({
            id: c.id || `char_${(i + 1).toString().padStart(3, "0")}`,
            name: c.name || (c as { name_suggestion?: string }).name_suggestion || "",
            nameEn: c.name_en || "",
            description: c.description || "",
            personality: c.personality || "",
            portrait_url: c.portrait_url || null,
          }));
        })(),
        plotPoints: (co.plot_points || []).map((p, i) => ({
          id: `pp_${i + 1}`,
          description: p.description || p.content || "",
          order: i + 1,
        })),
        // B42 fix: backend confirmed_outline_json uses field name "ending_options" (not "endings").
        // Use co.endings first for legacy compatibility, then co.ending_options as the real source.
        endings: (co.endings || co.ending_options || []).map((e, i) => ({
          id: e.id || `ending_${i + 1}`,
          description: e.description || "",
          isSelected: !!e.isSelected,
        })),
        mood: co.user_selected_mood || co.mood || "",
        // B42 fix: backend confirmed_outline_json has NO "scenes" field.
        // Stage 3 ScreenplayWriter stores scenes in project_chapters.scenes_json (NOT in confirmed_outline).
        // storyData comes from GET /chapters/1/story which returns chapter.scenes_json parsed as an array.
        // Priority: storyData.scenes (real chapter data) > co.scenes (legacy/empty fallback).
        scenes: (() => {
          const rawScenes = (() => {
            if (storyData?.scenes && Array.isArray(storyData.scenes) && storyData.scenes.length > 0) {
              // eslint-disable-next-line no-console
              console.log("[B42][hydrate] scenes source: storyData (chapter.scenes_json)", "count=", storyData.scenes.length);
              return storyData.scenes;
            }
            if (co.scenes && Array.isArray(co.scenes) && co.scenes.length > 0) {
              // eslint-disable-next-line no-console
              console.log("[B42][hydrate] scenes source: co.scenes (legacy)", "count=", co.scenes.length);
              return co.scenes as Array<{ id?: string; name?: string; description?: string; description_zh?: string; location_type?: string }>;
            }
            // eslint-disable-next-line no-console
            console.log("[B42][hydrate] scenes source: EMPTY — both storyData.scenes and co.scenes missing");
            return [] as Array<{ id?: string; name?: string; description?: string; description_zh?: string; location_type?: string; scene_id?: number; scene_heading?: string; location_id?: string; narration?: string }>;
          })();
          return rawScenes.map((s, i) => ({
            // Stage 3 scenes use scene_id (number) and scene_heading; legacy uses id (string) and name.
            id: (s as { id?: string; scene_id?: number }).id || String((s as { scene_id?: number }).scene_id ?? i + 1) || `scene_${i + 1}`,
            name: (s as { name?: string; scene_heading?: string }).name || (s as { scene_heading?: string }).scene_heading || "",
            description: (s as { description?: string; narration?: string }).description || (s as { narration?: string }).narration || "",
            description_zh: (s as { description_zh?: string }).description_zh,
            locationType: (s as { location_type?: string; location_id?: string }).location_type || (s as { location_id?: string }).location_id || "",
          }));
        })(),
      };
    }

    // Build previewCharacters with portrait_url (from chapter.characters_json)
    // D.21: storyData may be null if /chapters/1/story returned 400 (chapter in pending/generating_story state).
    // This is routine at character_ready stage — chapter has characters_json but full_script not yet written.
    const portraitByName: Record<string, string | null> = {};
    const portraitById: Record<string, string | null> = {};
    for (const cc of storyData?.characters || []) {
      if (cc.name) portraitByName[cc.name] = cc.portrait_url || null;
      if (cc.id) portraitById[cc.id] = cc.portrait_url || null;
    }

    // D.21: Static portrait URL fallback when storyData is null.
    // Backend writes: /static/outputs/{projectUuid}/character_refs/{char_id}_portrait.png
    // char_id format from confirmed_outline: "char_001", "char_002", etc. (see _map_outline_to_response, L107)
    const buildStaticPortraitUrl = (charId: string | null | undefined): string | null => {
      if (!charId || !projectUuid) return null;
      if (!/^char_\d+/.test(charId)) return null;
      return `/static/outputs/${projectUuid}/character_refs/${charId}_portrait.png`;
    };

    // [D.21] Log #7 — portrait lookup maps built from storyData
    // eslint-disable-next-line no-console
    console.log("[D.21][hydrate] portraitById keys:", Object.keys(portraitById), "portraitByName keys:", Object.keys(portraitByName));
    const previewCharacters: PreviewCharacter[] = outline
      ? outline.characters.map((c) => {
          // [D.21] Log #8 — per-character portrait resolution in hydrate path
          // eslint-disable-next-line no-console
          console.log("[D.21][hydrate] resolvePortraitForCharacter charId=", c.id, "name=", c.name);
          const apiPortraitUrl = portraitById[c.id] ?? portraitByName[c.name] ?? null;
          // eslint-disable-next-line no-console
          console.log("[D.21][hydrate] step 1 - API portrait_url:", apiPortraitUrl ?? "(empty)");
          const staticUrl = buildStaticPortraitUrl(c.id);
          // eslint-disable-next-line no-console
          console.log("[D.21][hydrate] step 2 - buildStaticPortraitUrl:", staticUrl ?? "(null)");
          const outlineUrl = c.portrait_url ?? null;
          // eslint-disable-next-line no-console
          console.log("[D.21][hydrate] step 3 - outline portrait_url:", outlineUrl ?? "(empty)");
          const finalUrl = apiPortraitUrl ?? staticUrl ?? outlineUrl ?? null;
          // eslint-disable-next-line no-console
          console.log("[D.21][hydrate] FINAL portrait src for", c.id, ":", finalUrl ?? "(NULL — will not render!)");
          return {
            id: c.id,
            name: c.name,
            description: c.description,
            fullbodyUrl: "/brand/logo-48.png",
            portraitUrl: finalUrl,
            adjustments: [],
          };
        })
      : [];

    // Wave 10 / RISK-T16-4: build previewScenes from the richest source available.
    // Priority: storyData.scenes (full Stage 3 payload with action_beats) > outline.scenes (4 fields only).
    // When storyData is available, spread the ENTIRE raw scene object so action_beats and all other
    // LLM fields survive to the confirm-scenes POST.
    const previewScenes: PreviewScene[] = (() => {
      if (storyData?.scenes && Array.isArray(storyData.scenes) && storyData.scenes.length > 0) {
        return storyData.scenes.map((s, i) => ({
          ...s,  // spread all LLM fields (action_beats, narration, location_id, etc.)
          id: s.id || String(s.scene_id ?? i + 1) || `scene_${i + 1}`,
          name: s.name || s.scene_heading || `场景${i + 1}`,
          description: s.description || s.narration || "",
          description_zh: s.description_zh,
          userEdit: "",
        }));
      }
      if (outline?.scenes && outline.scenes.length > 0) {
        return outline.scenes.map((s) => ({
          id: s.id,
          name: s.name,
          description: s.description_zh || s.description,
          userEdit: "",
        }));
      }
      return [];
    })();

    // Build shots from storyboard (only when generation completed)
    let shots: Shot[] = [];
    if (storyboardData?.storyboard) {
      const sb = storyboardData.storyboard as Record<string, unknown> | unknown[];
      const rawShots: unknown[] = Array.isArray(sb)
        ? sb
        : Array.isArray((sb as Record<string, unknown>)["shots"])
          ? ((sb as Record<string, unknown>)["shots"] as unknown[])
          : [];
      shots = rawShots.map((shot, i) => {
        const s = shot as Record<string, unknown>;
        const rawImageUrl = (s["image_url"] as string | null | undefined) || null;
        const rawImageUrlThumb = (s["image_url_thumb"] as string | null | undefined) || null;
        const textOverlay = s["text_overlay"] as { type?: string; text?: string } | undefined;
        return {
          shotId: (s["shot_id"] as number) || i + 1,
          sceneId:
            (s["scene_id"] as number) ||
            (s["original_scene_id"] as number) ||
            i + 1,
          imagePrompt: (s["image_prompt"] as string) || "",
          narrationSegment: (s["narration_segment"] as string) || "",
          shotType: (s["shot_type"] as string) || "medium shot",
          cameraAngle: (s["camera_angle"] as string) || "eye level",
          textType: textOverlay?.type || "narration",
          chineseText: textOverlay?.text ? [textOverlay.text] : [],
          imageUrl: toAbsoluteUrl(rawImageUrl),
          imageUrlThumb: toAbsoluteUrl(rawImageUrlThumb),
          charactersInScene: (s["characters_in_scene"] as string[]) || [],
          // B44: read safety_advice + error fields written back by Stage 5 pipeline
          success: s["success"] !== undefined ? (s["success"] as boolean) : (rawImageUrl != null),
          errorKind: (s["error_kind"] as string | null | undefined) || null,
          errorMessage: (s["error_message"] as string | null | undefined) || null,
          safetyAdvice: (s["safety_advice"] as SafetyAdvice | null | undefined) || null,
        };
      });
    }

    // Best-effort BGM info — BUG-T13-PREVIEW-DIRECT-LOAD-SLOW: now fetched in the parallel
    // batch above (no separate sequential fetch). Use bgmInfo from that batch directly.
    let bgmUrl: string | null = null;
    if (bgmInfo && bgmInfo.bgm_exists && bgmInfo.bgm_url) {
      bgmUrl = toAbsoluteUrl(bgmInfo.bgm_url);
    }

    // Map reconciled URL stage → CreateStage / GenerationSubPhase for hydrate payload
    const { currentStage, subPhase } = stateFromUrlStage(reconciledStage);

    // Determine generationStatus: if backend completed → "complete", else "generating", else "idle"
    let generationStatus: "idle" | "generating" | "complete" | "error" = "idle";
    if (status.status === "completed") generationStatus = "complete";
    else if (status.status === "generating") generationStatus = "generating";
    else if (status.status === "failed") generationStatus = "error";

    const hydratePayload = {
      projectId: projectUuid,
      currentStage,
      generationSubPhase: subPhase ?? "text-gen",
      idea: project.original_idea || "",
      stylePreset: project.style_preset || null,
      aspectRatio: (project.aspect_ratio || "2:3") as AspectRatio,
      // B33: hydrate user_selected_mood from backend ProjectDetail
      userSelectedMood: project.user_selected_mood ?? null,
      outline,
      outlineConfirmed: !!outline && status.status !== "pending",
      previewCharacters,
      previewScenes,
      charactersConfirmed,
      scenesConfirmed,
      shots,
      generationStatus,
      generationProgress: status.progress || 0,
      generationMessage: status.message || "",
      bgmPlayer: bgmUrl
        ? {
            status: "ready" as const,
            bgmUrl,
            volume: 70,
            metaVersion: null,
            creditsUsed: 0,
            errorMessage: null,
          }
        : undefined,
    };

    return { hydratePayload, reconciledStage, notFound: false };
  } catch (err) {
    // Unexpected error in chapter hydration logic (not a 404 — those are caught above).
    // notFound stays false so caller shows a generic "load failed, retry" error
    // rather than the misleading "项目不存在或已删除" message.
    console.error("[hydrate] unexpected error during chapter hydration:", err);
    return { hydratePayload: null, reconciledStage: urlStage, notFound: false };
  }
}

interface CreateContentProps {
  urlProjectUuid?: string;
  urlStage?: string;
}

export default function CreateContent({ urlProjectUuid, urlStage }: CreateContentProps = {}) {
  const { state, dispatch } = useCreate();
  const router = useRouter();
  const { isLoggedIn, loadingUser } = useAuth();

  // UX-16: hydration tracking — prevents redundant fetches per project.
  const hydratedFor = useRef<string | null>(null);
  // Start in hydrating=true only when URL has a projectUuid (deep-link / F5).
  // For in-session navigation (state→URL push), we'll immediately set hydrating=false in the effect.
  const [hydrating, setHydrating] = useState(!!urlProjectUuid);
  const [hydrateError, setHydrateError] = useState<string | null>(null);
  // B28: track when hydrate is pending due to backend slow-response (vs genuine failure)
  const [hydrateSlowWarning, setHydrateSlowWarning] = useState(false);

  // UX-16: track the last URL we pushed so the URL→state effect can ignore the echo.
  const lastPushedUrlRef = useRef<string | null>(null);

  // ──────────────────────────────────────────────────────────────────────────
  // Hydration: when the page mounts with a URL projectUuid, fetch backend data.
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!urlProjectUuid) {
      setHydrating(false);
      return;
    }
    // Already hydrated this exact project this session → skip
    if (hydratedFor.current === urlProjectUuid && state.projectId === urlProjectUuid) {
      setHydrating(false);
      return;
    }
    // Spinner-loop guard: if the URL change was triggered by our own state→URL push (lastPushedUrlRef),
    // and state.projectId already matches urlProjectUuid (in-session navigation, not deep-link),
    // skip hydration. This prevents the 1-2 min spinner every time subPhase changes push a new URL.
    // Example: active create session pushes /generating → /characters on character_ready;
    //          without this guard every URL change triggers a full backend hydrate.
    const currentUrl = typeof window !== "undefined" ? window.location.pathname : null;
    const isOurOwnPush = lastPushedUrlRef.current === currentUrl;
    if (isOurOwnPush && state.projectId === urlProjectUuid) {
      setHydrating(false);
      return;
    }
    // RISK-T20-11 (2026-05-19): in-session create flow guard.
    // StageA does `router.replace(/create/{uuid}/outline)` after generating outline.
    // That push happens outside CreateContent's state→URL effect, so `lastPushedUrlRef`
    // isn't set and the `isOurOwnPush` check above misses. Without this guard, the
    // hydrate effect re-fetches the entire project (including a 30s+ /chapters/1/story
    // 404 retry loop) just after StageA already dispatched SET_OUTLINE — Founder test17
    // v2 saw "大纲直接在 /create 出来了 停留 /create 地址, 10s 内跳到 /outline 显示载入中,
    // 过了 30s 又出来". When state.projectId matches urlProjectUuid AND we already have
    // outline data in memory, we can safely skip the backend hydrate (data is fresher
    // than any backend echo would be).
    if (state.projectId === urlProjectUuid && state.outline !== null) {
      // eslint-disable-next-line no-console
      console.log("[hydrate] RISK-T20-11 skip: in-session project already has outline data, no re-fetch needed");
      hydratedFor.current = urlProjectUuid;
      lastPushedUrlRef.current = currentUrl;
      setHydrating(false);
      return;
    }
    // If we're still figuring out auth, wait
    if (loadingUser) return;

    if (!isLoggedIn) {
      router.replace("/login");
      return;
    }

    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    const safeUrlStage: UrlStage = isUrlStage(urlStage) ? urlStage : "outline";

    setHydrating(true);
    setHydrateError(null);
    setHydrateSlowWarning(false);

    // B28: Show "正在等待服务器..." hint after 15s to reassure user
    const slowHintTimer = setTimeout(() => setHydrateSlowWarning(true), 15000);

    void (async () => {
      const result = await hydrateProjectFromBackend(urlProjectUuid, token, safeUrlStage);
      clearTimeout(slowHintTimer);
      setHydrateSlowWarning(false);
      if (result.notFound) {
        setHydrateError("项目不存在或已删除");
        setHydrating(false);
        return;
      }
      if (!result.hydratePayload) {
        // B28: hydratePayload null means project fetch timed out (120s) or had a non-404 error.
        // This is most likely the backend being temporarily unavailable (Stage 3 LLM blocking).
        // Don't show a hard error — show a soft "retry" message with a refresh prompt.
        setHydrateError("服务器正忙（AI 正在创作中），请稍后刷新重试");
        setHydrating(false);
        return;
      }

      // P0 hotfix v2: If outline is null but we're at the outline stage (pre-confirm,
      // backend has raw_outline_json but ProjectDetail doesn't expose it), re-fetch
      // the outline via generate-outline which is idempotent for already-generated projects.
      // This happens when user refreshes at /create/{uuid}/outline before confirming.
      let finalPayload = result.hydratePayload;
      if (
        finalPayload.outline === null &&
        (result.reconciledStage === "outline" || safeUrlStage === "outline")
      ) {
        console.info("[hydrate] outline null at /outline stage — recovering via generate-outline");
        try {
          const recoveredOutline = await apiFetch<StoryOutline>(
            `/projects/${urlProjectUuid}/generate-outline`,
            { method: "POST" },
            token
          );
          finalPayload = { ...finalPayload, outline: recoveredOutline };
          console.info("[hydrate] outline recovered successfully");
        } catch (err) {
          // Non-fatal: if recovery fails, dispatch without outline.
          // StageB will show a user-friendly error rather than blank screen.
          console.warn("[hydrate] outline recovery failed:", err instanceof Error ? err.message : err);
        }
      }

      hydratedFor.current = urlProjectUuid;
      dispatch({ type: "HYDRATE_FROM_BACKEND", payload: finalPayload });

      // If backend reconciled to a different stage than the URL says, redirect.
      if (result.reconciledStage !== safeUrlStage) {
        const newUrl = buildCreateUrl(urlProjectUuid, result.reconciledStage);
        // [Router] Log #9 — hydration redirect decision
        // eslint-disable-next-line no-console
        console.log("[Router] hydrate redirect:", { from: safeUrlStage, to: result.reconciledStage, newUrl, reason: "reconcileBackendVsUrl overrode URL stage" });
        if (newUrl) {
          lastPushedUrlRef.current = newUrl;
          router.replace(newUrl);
        }
      } else {
        // [Router] Log #10 — hydration: URL stage already correct, no redirect needed
        // eslint-disable-next-line no-console
        console.log("[Router] hydrate no redirect needed, URL stage matches reconciledStage:", safeUrlStage);
        lastPushedUrlRef.current = `/create/${urlProjectUuid}/${safeUrlStage}`;
      }
      setHydrating(false);
    })();
  // RISK-T20-11: state.outline is intentionally not in the dep array — the in-session
  // skip guard reads it ad-hoc at effect start. Adding it would cause the effect to
  // re-run every time outline state changes (e.g. when SET_OUTLINE dispatches), which
  // would defeat the guard and re-trigger hydration unnecessarily.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlProjectUuid, urlStage, isLoggedIn, loadingUser, dispatch, router, state.projectId]);

  // ──────────────────────────────────────────────────────────────────────────
  // State → URL sync: whenever currentStage / subPhase / projectId changes,
  // compute the canonical URL and replace if it differs from current pathname.
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    // Skip until hydration is complete (avoid stomping the redirect above)
    if (hydrating) return;

    const desiredStage = deriveUrlStageFromState(state.currentStage, state.generationSubPhase);
    const projectId = state.projectId;

    // No project yet (Stage A) — should be at /create. Don't push.
    if (!projectId || !desiredStage) return;

    const desiredUrl = buildCreateUrl(projectId, desiredStage);
    if (!desiredUrl) return;

    // Read current pathname directly to avoid stale closure
    const currentPath = typeof window !== "undefined" ? window.location.pathname : null;
    if (currentPath === desiredUrl) {
      lastPushedUrlRef.current = desiredUrl;
      return;
    }

    lastPushedUrlRef.current = desiredUrl;
    // UX-16 nav semantics:
    //   - Use router.push so each semantic stage transition (outline → generating
    //     → characters → scenes → generating → preview → delivery) creates a
    //     browser history entry. Back button returns user to previous stage.
    //   - This effect ONLY fires when state.currentStage / subPhase / projectId
    //     change — pollers and progress ticks DON'T trigger it. So we won't pollute
    //     history with one entry per poll. (Each push corresponds to a real stage.)
    //   - Hydration redirects use router.replace separately (in the hydrate effect)
    //     to avoid creating a back-button trap that loops to the same URL.
    router.push(desiredUrl);
  }, [
    state.currentStage,
    state.generationSubPhase,
    state.projectId,
    hydrating,
    router,
  ]);

  // ──────────────────────────────────────────────────────────────────────────
  // BUG-T13-* FIX: Top-level backend status watcher (safety net for auto-jump).
  //
  // StageC owns the primary text-gen / shot-gen / checkpoint pollers that handle
  // transitions when subPhase is text-gen / char-preview / scene-preview / shot-gen.
  // But test13 exposed gaps where those pollers can fall silent (closure stale,
  // React anti-pattern stops re-render, StageC unmounts during transition, etc),
  // leaving users stuck on /generating while backend has reached character_ready /
  // scenes_ready / completed.
  //
  // This watcher polls every 5s INDEPENDENTLY of StageC and force-routes when:
  //   - status.stage === "character_ready" + !charactersConfirmed → /characters
  //     (BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP)
  //   - status.stage === "scenes_ready" + charactersConfirmed + !scenesConfirmed → /scenes
  //   - status.status === "completed" → /preview
  //     (BUG-T13-COMPLETED-NO-AUTO-JUMP)
  //
  // 5s interval (not 2s) since StageC's 2s poller is still the primary; this is fallback.
  // Reads latest state from refs so the interval doesn't reset on every state tick.
  // ──────────────────────────────────────────────────────────────────────────
  // Live refs for state values read inside the watcher (avoid re-creating the
  // interval every time these flip).
  const watcherCharactersConfirmedRef = useRef(state.charactersConfirmed);
  watcherCharactersConfirmedRef.current = state.charactersConfirmed;
  const watcherScenesConfirmedRef = useRef(state.scenesConfirmed);
  watcherScenesConfirmedRef.current = state.scenesConfirmed;
  const watcherCurrentStageRef = useRef(state.currentStage);
  watcherCurrentStageRef.current = state.currentStage;
  const watcherGenerationStatusRef = useRef(state.generationStatus);
  watcherGenerationStatusRef.current = state.generationStatus;
  // Wave 9 / DEC-030 顺解 T15-8: track current subPhase so we only dispatch
  // SET_GENERATION_SUB_PHASE when it actually differs from the derived value.
  // Without this, every 5s tick would dispatch the same value, causing
  // unnecessary re-renders cascading through StageC + its child checkpoints.
  const watcherSubPhaseRef = useRef(state.generationSubPhase);
  watcherSubPhaseRef.current = state.generationSubPhase;

  useEffect(() => {
    if (hydrating) return;
    if (!state.projectId || state.projectId !== urlProjectUuid) return;
    if (!isLoggedIn) return;
    const token = getStoredToken();
    if (!token) return;

    let cancelled = false;
    const projectId = state.projectId;

    const checkAndRoute = async () => {
      if (cancelled) return;
      // Read latest stage/status from refs (no stale closure)
      const currentStageNow = watcherCurrentStageRef.current;
      const generationStatusNow = watcherGenerationStatusRef.current;
      // Skip if user is at terminal stage or in error
      if (currentStageNow === "preview" || currentStageNow === "deliver") return;
      if (generationStatusNow === "error") return;

      try {
        // RISK-T20-11.v2 (Wave 4): Suppress 404 console.warn during /outline phase.
        // Chapter is created only after user clicks 确认大纲 (POST /confirm-outline).
        // Before that, every 5s tick of this Watcher polls /chapters/1/status which 404s.
        // Founder test19 实证: 4 min /outline 停留累积 ~48 个 404 console noise.
        // These 4xx are by-design (chapter not created yet), not bugs — silently caught.
        const status = await apiFetch<ChapterStatusResp>(
          `/projects/${projectId}/chapters/1/status`,
          {},
          token,
          { silentStatuses: [404] },
        );
        if (cancelled) return;

        const currentPath = typeof window !== "undefined" ? window.location.pathname : null;
        const charactersConfirmedNow = watcherCharactersConfirmedRef.current;
        const scenesConfirmedNow = watcherScenesConfirmedRef.current;

        // ============================================================================
        // Wave 9 / DEC-030 顺解 T15-8: derive generationSubPhase from backend ui_phase.
        // ============================================================================
        // Previously generationSubPhase was only flipped by user click handlers
        // (handleConfirmCharacters / handleConfirmScenes). If PM force-unblocked R4-2 via
        // direct POST /confirm-scenes, or if user refreshed mid-pipeline, subPhase stayed
        // stale → e.g. /generating "后台生成" button hidden during shot-gen because
        // subPhase was frozen at text-gen.
        //
        // Now: every 5s, if backend ui_phase indicates a phase that has a known subPhase
        // mapping AND it differs from current state, we dispatch the correction.
        // This works alongside (not replacing) the user click path — they will converge.
        if (status.ui_phase) {
          // T21-NEW-7 (2026-05-21 DEC-047 v1.4): 9 状态机 — 加 scene_references_review → scene-refs-preview
          const uiPhaseToSubPhase: Record<
            string,
            "text-gen" | "char-preview" | "scene-refs-preview" | "shot-gen" | null
          > = {
            input: null, // no project / no generation — leave subPhase alone
            outline_review: null, // user in StageB — leave alone
            char_review_pending: "text-gen", // Stage 1/2 running
            char_review: "char-preview", // R4-1 user checkpoint
            scene_review_pending: "text-gen", // Stage 3 running
            // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene_review → scene-preview 映射已移除.
            //   Backend Wave 8 会同步移除 scene_review ui_phase + R4-2 wait loop.
            //   如果 backend 仍发 scene_review (未 Wave 8), 前端 fallthrough → text-gen (无 map key)
            storyboard_running: "text-gen", // Stage 4 LLM 或 Stage 4.5 anchor 生成中
            // T21-NEW-7 v1.4: R4-3 用户确认场景参考图 (镜像 char-preview 对偶设计, 保留).
            scene_references_review: "scene-refs-preview",
            shot_generating: "shot-gen", // Stage 5 + image_prep + bgm
            completed: "shot-gen", // post-completion subPhase parks at shot-gen until /preview transition
          };
          let derivedSubPhase = uiPhaseToSubPhase[status.ui_phase];
          // RISK-T20-25 (Wave 4): If local state already says user confirmed characters,
          // do NOT override subPhase back to char-preview from stale backend ui_phase=char_review.
          // Backend has ~200-500ms latency to process /confirm-characters; during that window
          // ui_phase=char_review is stale. Local CONFIRM_CHARACTERS dispatch is authoritative.
          // Same rationale for scenes: if user clicked confirm scenes locally, don't go back to scene-preview.
          if (
            derivedSubPhase === "char-preview" &&
            charactersConfirmedNow
          ) {
            // Override: derive text-gen instead (matches scene_review_pending semantic)
            derivedSubPhase = "text-gen";
          }
          // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene-preview + scenesConfirmedNow race guard 已移除.
          //   旧 guard: "derivedSubPhase === 'scene-preview' && scenesConfirmedNow → shot-gen"
          //   现在 scene_review ui_phase 不再映射 scene-preview, race guard 无需存在.
          // T21-NEW-7 v1.4: 对偶 scene-refs-preview 保护 — 如果用户已确认场景参考图 (本地状态)
          //   但 backend 还在 ui_phase=scene_references_review (~200ms 延迟), 不重置 subPhase.
          //   用 status.scene_references_confirmed 直读判断 (backend authoritative + 本地 race 都覆盖).
          if (
            derivedSubPhase === "scene-refs-preview" &&
            status.scene_references_confirmed === true
          ) {
            derivedSubPhase = "shot-gen";
          }
          // Compare against current subPhase via ref to avoid spurious re-renders.
          // Only dispatch when derived value is non-null AND differs from current.
          if (derivedSubPhase !== null && derivedSubPhase !== watcherSubPhaseRef.current) {
            // eslint-disable-next-line no-console
            console.log(
              "[Watcher] Wave9: ui_phase=",
              status.ui_phase,
              "→ derived subPhase=",
              derivedSubPhase,
              "(was:",
              watcherSubPhaseRef.current,
              ") — dispatching SET_GENERATION_SUB_PHASE",
            );
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: derivedSubPhase });
          }
        }

        // ── Force /preview when backend completed ─────────────────────────
        // Wave 9: prefer ui_phase=completed over (status/stage/progress) triad
        const isCompleted =
          status.ui_phase === "completed" ||
          status.status === "completed" ||
          status.stage === "completed" ||
          status.progress >= 100;
        if (isCompleted) {
          const previewUrl = buildCreateUrl(projectId, "preview");
          if (previewUrl && currentPath !== previewUrl) {
            // eslint-disable-next-line no-console
            console.log("[Watcher] backend completed but URL is", currentPath, "→ force /preview (ui_phase=", status.ui_phase, ")");
            lastPushedUrlRef.current = previewUrl;
            router.replace(previewUrl);
          }
          return;
        }

        // ── Force /characters when at char_review (Wave 9) or character_ready + !confirmed (legacy) ───
        // RISK-T20-25 (Wave 4): also gate Wave 9 path on `!charactersConfirmedNow`. Reason:
        //   - User locally confirms (handleConfirmCharacters dispatches CONFIRM_CHARACTERS + subPhase=text-gen)
        //   - But confirm-characters API await is in flight (~200-500ms latency)
        //   - During that window backend still returns ui_phase=char_review
        //   - Watcher previously force-routed back to /characters, causing /characters→/generating→/characters race
        //   - charactersConfirmedNow=true (local state, set via dispatch CONFIRM_CHARACTERS) means user has
        //     already clicked, so respect the local intent and skip the force-route.
        //   - Once API completes, backend ui_phase→scene_review_pending, this branch becomes false naturally.
        const isCharReview =
          (status.ui_phase === "char_review" && !charactersConfirmedNow) ||
          (status.stage === "character_ready" && !charactersConfirmedNow);
        if (isCharReview) {
          const charsUrl = buildCreateUrl(projectId, "characters");
          if (charsUrl && currentPath !== charsUrl) {
            // eslint-disable-next-line no-console
            console.log("[Watcher] char_review (ui_phase=", status.ui_phase, ") but URL is", currentPath, "→ force /characters");
            lastPushedUrlRef.current = charsUrl;
            // Also update state so StageC renders CharacterPreview
            if (currentStageNow !== "generate") {
              dispatch({ type: "SET_STAGE", payload: "generate" });
            }
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "char-preview" });
            router.replace(charsUrl);
          }
          return;
        }

        // T22-NEW-5 (2026-05-22): 砍 R4-2 — isSceneReview force-route 分支已整段移除.
        //   旧逻辑: ui_phase=scene_review → force /scenes + dispatch scene-preview + hydrate /story
        //   新逻辑: Pipeline 直接 Stage 3 → Stage 4, 无 R4-2 文字层场景确认闸门.
        //   Backend Wave 8 会同步移除: pipeline_orchestrator.py R4-2 wait loop +
        //     STATUS_API_CONTRACT v1.5 (移除 scene_review ui_phase) +
        //     chapters.py confirm-scenes endpoint 处理.
        //   部署铁律: 本 Frontend 改动暂不部署, 等 Backend Wave 8 完成后同步上线.

        // ── T21-NEW-7 v1.4 (2026-05-21 DEC-047): Force /scenes when at scene_references_review (R4-3) ──
        // 镜像 isCharReview / isSceneReview 模式. 当 Stage 4.5 完成 + 用户尚未确认时强制 /scenes.
        //   gate on `!status.scene_references_confirmed`: 用户已点确认时 backend 仍可能短暂返
        //   scene_references_review (~200ms race), 不重复把用户拉回此页面.
        const isSceneRefsReview =
          status.ui_phase === "scene_references_review" &&
          !status.scene_references_confirmed;
        if (isSceneRefsReview) {
          const scenesUrl = buildCreateUrl(projectId, "scenes");
          if (scenesUrl && currentPath !== scenesUrl) {
            // eslint-disable-next-line no-console
            console.log("[Watcher] T21-NEW-7 v1.4: scene_references_review but URL is", currentPath, "→ force /scenes");
            lastPushedUrlRef.current = scenesUrl;
            if (currentStageNow !== "generate") {
              dispatch({ type: "SET_STAGE", payload: "generate" });
            }
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "scene-refs-preview" });
            router.replace(scenesUrl);
          }
          // 即使 URL 已经在 /scenes, 也确保 subPhase 是 scene-refs-preview (不是 scene-preview)
          // 防止 URL 刚 settle 时 stale subPhase 渲染错组件
          if (watcherSubPhaseRef.current !== "scene-refs-preview") {
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "scene-refs-preview" });
          }
          return;
        }

        // ── RISK-T14-8 / Wave 9: Force /generating when in storyboard_running / shot_generating
        // (or legacy MID_PIPELINE_STAGES) while URL is /scenes. Prevents user from being stuck
        // on /scenes "scene generating" spinner after scenes have actually been confirmed and
        // pipeline has moved on.
        // T21-NEW-7 v1.4 NOTE: Stage 4.5 跑中 ui_phase=storyboard_running, 此分支会把用户从 /scenes
        //   拉回 /generating (符合预期 — 用户应等 Stage 4.5 跑完). 完成后 ui_phase=scene_references_review
        //   走上一个 isSceneRefsReview 分支再拉回 /scenes 给真预览.
        const MID_PIPELINE_STAGES = ["storyboard", "image_preparation", "image_generation", "bgm"];
        const isShotPhase =
          status.ui_phase === "storyboard_running" ||
          status.ui_phase === "shot_generating" ||
          (scenesConfirmedNow && status.stage !== null && MID_PIPELINE_STAGES.includes(status.stage));
        if (isShotPhase) {
          const generatingUrl = buildCreateUrl(projectId, "generating");
          const isOnScenes = currentPath?.endsWith("/scenes");
          if (generatingUrl && isOnScenes) {
            // eslint-disable-next-line no-console
            console.log("[Watcher] RISK-T14-8 / Wave9: ui_phase=", status.ui_phase, "stage=", status.stage, "but URL is /scenes → force /generating");
            lastPushedUrlRef.current = generatingUrl;
            if (currentStageNow !== "generate") {
              dispatch({ type: "SET_STAGE", payload: "generate" });
            }
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "shot-gen" });
            router.replace(generatingUrl);
          }
          return;
        }
      } catch (err) {
        // Non-fatal: ignore poll errors (StageC's poller will catch real issues)
        // eslint-disable-next-line no-console
        console.warn("[Watcher] status poll failed (non-fatal):", err instanceof Error ? err.message : err);
      }
    };

    // Initial check immediately, then every 5s. State changes don't restart this interval;
    // refs above provide fresh values without dep churn.
    void checkAndRoute();
    const intervalId = setInterval(checkAndRoute, 5000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [
    hydrating,
    state.projectId,
    urlProjectUuid,
    isLoggedIn,
    router,
    dispatch,
  ]);

  // ──────────────────────────────────────────────────────────────────────────
  // URL → state sync: when user navigates back/forward, urlStage prop changes.
  // Update React state to match (only if it doesn't already match what state implies).
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (hydrating) return;
    if (!urlProjectUuid || !urlStage) return;
    if (!isUrlStage(urlStage)) return;
    // Only act once initial hydration has completed and projectId matches URL.
    if (state.projectId !== urlProjectUuid) return;

    const derivedFromState = deriveUrlStageFromState(state.currentStage, state.generationSubPhase);
    if (derivedFromState === urlStage) return; // already in sync

    // Echo guard: if the URL change was triggered by us, skip.
    const echoUrl = lastPushedUrlRef.current;
    const incomingUrl = `/create/${urlProjectUuid}/${urlStage}`;
    if (echoUrl === incomingUrl) return;

    // UX-16 protection: if generation is already complete and user back-navigates
    // into a pre-completion stage, force them back to /preview. The pipeline can't
    // be re-run; allowing them into "generating" would restart pollers harmfully.
    const completedRedirectStages: UrlStage[] = ["generating", "characters", "scenes", "outline"];
    if (
      state.generationStatus === "complete" &&
      completedRedirectStages.includes(urlStage)
    ) {
      const preview = buildCreateUrl(urlProjectUuid, "preview");
      if (preview) {
        lastPushedUrlRef.current = preview;
        router.replace(preview);
      }
      return;
    }

    // URL stage differs from state → adopt URL (user pressed back/forward)
    const { currentStage, subPhase } = stateFromUrlStage(urlStage);
    dispatch({ type: "SET_STAGE", payload: currentStage });
    if (subPhase) {
      dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: subPhase });
    }
  }, [
    urlStage,
    urlProjectUuid,
    state.projectId,
    state.currentStage,
    state.generationSubPhase,
    state.generationStatus,
    hydrating,
    dispatch,
    router,
  ]);

  // Wave 13 #4A (P2-2 fix): during the CONFIRMATION FLOW (urlStage ∈ outline/characters/scenes)
  // a hydrate timeout must NOT dump the user to "返回工作台" — they still have to come back and
  // confirm characters/scenes, so leaving would break the flow. Instead we auto-retry the page a
  // few times (the story keeps generating server-side) before falling back to a manual refresh.
  // Pure generation / preview / delivery stages keep "返回工作台" (safe to leave — nothing to confirm).
  const inConfirmationFlow =
    urlStage === "outline" || urlStage === "characters" || urlStage === "scenes";
  const isHydrateTimeout = !!hydrateError && hydrateError.includes("服务器正忙");

  useEffect(() => {
    // Auto-retry only while in the confirmation flow on a timeout. Bounded by a per-project
    // sessionStorage counter so we never loop forever if the backend stays down — after the cap
    // we stop auto-retrying and leave the user with the manual "刷新页面，继续等待" button.
    if (!isHydrateTimeout || !inConfirmationFlow || !urlProjectUuid) return;
    if (typeof window === "undefined") return;

    const KEY = `hydrate_autoretry_${urlProjectUuid}`;
    const MAX_AUTO_RETRIES = 3;
    const count = Number(window.sessionStorage.getItem(KEY) || "0");
    if (count >= MAX_AUTO_RETRIES) return; // give up auto-retry, user can still refresh manually

    const timer = setTimeout(() => {
      window.sessionStorage.setItem(KEY, String(count + 1));
      // eslint-disable-next-line no-console
      console.log(`[#4A] confirmation-flow hydrate timeout — auto-retry ${count + 1}/${MAX_AUTO_RETRIES}`);
      window.location.reload();
    }, 8000);
    return () => clearTimeout(timer);
  }, [isHydrateTimeout, inConfirmationFlow, urlProjectUuid]);

  // ──────────────────────────────────────────────────────────────────────────
  // Render
  // ──────────────────────────────────────────────────────────────────────────

  // UX-16: hydrating spinner (URL deep link / refresh)
  if (urlProjectUuid && hydrating) {
    return (
      <div className="min-h-screen bg-bg-primary">
        <CreateHeader />
        <main className="container-lg py-8 pb-24">
          <div className="max-w-lg mx-auto text-center pt-20">
            <Loader2 className="w-8 h-8 text-brand-primary mx-auto mb-3 animate-spin" />
            <p className="text-text-muted text-sm">正在加载你的故事...</p>
            {/* B28: Show slow-warning after 15s so user knows we're waiting on backend, not hung */}
            {hydrateSlowWarning && (
              <p className="text-text-muted text-xs mt-3 opacity-70">
                AI 正在创作中，服务器响应稍慢，请耐心等待...
              </p>
            )}
          </div>
        </main>
      </div>
    );
  }

  if (urlProjectUuid && hydrateError) {
    // B28: Distinguish timeout ("AI still working") from genuine 404 ("project gone").
    // Timeout should offer a retry path — NOT auto-redirect to /outline.
    const isTimeout = isHydrateTimeout;
    return (
      <div className="min-h-screen bg-bg-primary">
        <CreateHeader />
        <main className="container-lg py-8 pb-24">
          <div className="max-w-lg mx-auto text-center pt-20">
            {isTimeout ? (
              <>
                <Loader2 className="w-10 h-10 text-brand-primary mx-auto mb-4 animate-spin" />
                <h2 className="text-lg font-semibold text-text-primary mb-2">AI 正在努力创作中</h2>
                {/* Wave 13 #4A: in the confirmation flow, reassure + auto-retry, do NOT offer
                    "返回工作台" (would interrupt — user still needs to confirm characters/scenes).
                    In pure generation/preview/delivery, keep "返回工作台" (safe to leave). */}
                {inConfirmationFlow ? (
                  <p className="text-text-secondary text-sm mb-6">
                    服务器繁忙或 AI 创作耗时较长，正在自动为你重试…<br />
                    你正在创作流程中，请稍候——确认环节马上回来，不需要重新开始。
                  </p>
                ) : (
                  <p className="text-text-secondary text-sm mb-6">
                    服务器繁忙或 AI 创作耗时较长，请稍后重试。<br />
                    你的故事正在后台继续生成，不需要重新开始。
                  </p>
                )}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={() => {
                      // eslint-disable-next-line no-console
                      console.log("[B28] user clicked retry hydrate, projectUuid=", urlProjectUuid);
                      window.location.reload();
                    }}
                    className="btn-primary px-6"
                  >
                    刷新页面，继续等待
                  </button>
                  {/* #4A: "返回工作台" only outside the confirmation flow */}
                  {!inConfirmationFlow && (
                    <button
                      onClick={() => router.replace("/dashboard")}
                      className="px-6 py-2 rounded-lg border border-white/20 text-text-secondary hover:bg-white/5 transition-colors text-sm font-medium"
                    >
                      返回工作台
                    </button>
                  )}
                </div>
                <p className="text-text-muted text-xs mt-4">
                  {inConfirmationFlow
                    ? "页面会自动重试，请保持打开"
                    : "也可以关闭页面——完成后在工作台中查看"}
                </p>
              </>
            ) : (
              <>
                <AlertCircle className="w-8 h-8 text-error mx-auto mb-3" />
                <p className="text-text-secondary text-sm mb-4">{hydrateError}</p>
                <button
                  onClick={() => router.replace("/dashboard")}
                  className="btn-primary px-8"
                >
                  返回工作台
                </button>
              </>
            )}
          </div>
        </main>
      </div>
    );
  }

  const renderStage = () => {
    switch (state.currentStage) {
      case "input":
        return <StageA />;
      case "confirm":
        return <StageB />;
      case "generate":
        return <StageC />;
      case "preview":
        return <StageD />;
      case "deliver":
        return <StageE />;
      default:
        return <StageA />;
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <CreateHeader />
      {renderStage()}
    </div>
  );
}
