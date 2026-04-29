"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken, fetchBgmInfo } from "@/lib/api";
import { mockOutline } from "@/lib/mock-data";
import type {
  StoryOutline,
  StoryLength,
  Shot,
  PreviewCharacter,
  PreviewScene,
  AspectRatio,
} from "@/types/create";
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

interface ChapterStatusResp {
  status: string;
  stage: string | null;
  progress: number;
  message: string;
  estimated_remaining_seconds?: number | null;
}

interface ProjectDetailResp {
  id: string;
  title: string;
  original_idea: string;
  style_preset: string;
  aspect_ratio: string | null;
  created_at: string;
  confirmed_outline?: {
    title?: string;
    title_en?: string;
    summary?: string;
    mood?: string;
    user_selected_mood?: string | null;
    plot_points?: Array<{ description?: string; content?: string }>;
    characters?: Array<{
      id?: string;
      name?: string;
      name_en?: string;
      description?: string;
      personality?: string;
      portrait_url?: string | null;
    }>;
    scenes?: Array<{ id?: string; name?: string; description?: string; description_zh?: string; location_type?: string }>;
    endings?: Array<{ id?: string; description?: string; isSelected?: boolean }>;
  } | null;
}

interface ChapterStoryResp {
  characters?: Array<{ id?: string; name: string; description?: string; portrait_url?: string | null }>;
  scenes?: Array<{ scene_id?: number; visual_description?: string; narration?: string }>;
}

interface StoryboardResp {
  storyboard: unknown;
  chapter_number: number;
  project_id: string;
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
  try {
    // Pull project + status (always needed)
    const [project, status] = await Promise.all([
      apiFetch<ProjectDetailResp>(`/projects/${projectUuid}`, {}, token),
      apiFetch<ChapterStatusResp>(`/projects/${projectUuid}/chapters/1/status`, {}, token).catch(
        () => ({ status: "pending", stage: null, progress: 0, message: "" } as ChapterStatusResp)
      ),
    ]);

    // Pull storyboard + story (best-effort — empty if not yet generated)
    const [storyboardData, storyData] = await Promise.all([
      apiFetch<StoryboardResp>(`/projects/${projectUuid}/chapters/1/storyboard`, {}, token).catch(
        () => null
      ),
      apiFetch<ChapterStoryResp>(`/projects/${projectUuid}/chapters/1/story`, {}, token).catch(
        () => null
      ),
    ]);

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
    const charactersConfirmed =
      ADVANCED_STAGES.has(status.stage || "") || status.status === "completed";
    const scenesConfirmed =
      ADVANCED_STAGES.has(status.stage || "") || status.status === "completed";

    const reconciledStage = reconcileBackendVsUrl({
      urlStage,
      backendStatus: status.status,
      backendStage: status.stage,
      charactersConfirmed,
      scenesConfirmed,
    });

    // Build outline from confirmed_outline (or null if user hasn't confirmed yet)
    const co = project.confirmed_outline;
    let outline: StoryOutline | null = null;
    if (co) {
      outline = {
        title: co.title || project.title || "",
        titleEn: co.title_en || "",
        summary: co.summary || "",
        characters: (co.characters || []).map((c, i) => ({
          id: c.id || `char_${i + 1}`,
          name: c.name || "",
          nameEn: c.name_en || "",
          description: c.description || "",
          personality: c.personality || "",
          portrait_url: c.portrait_url || null,
        })),
        plotPoints: (co.plot_points || []).map((p, i) => ({
          id: `pp_${i + 1}`,
          description: p.description || p.content || "",
          order: i + 1,
        })),
        endings: (co.endings || []).map((e, i) => ({
          id: e.id || `ending_${i + 1}`,
          description: e.description || "",
          isSelected: !!e.isSelected,
        })),
        mood: co.user_selected_mood || co.mood || "",
        scenes: (co.scenes || []).map((s, i) => ({
          id: s.id || `scene_${i + 1}`,
          name: s.name || "",
          description: s.description || "",
          description_zh: s.description_zh,
          locationType: s.location_type || "",
        })),
      };
    }

    // Build previewCharacters with portrait_url (from chapter.characters_json)
    const portraitByName: Record<string, string | null> = {};
    const portraitById: Record<string, string | null> = {};
    for (const cc of storyData?.characters || []) {
      if (cc.name) portraitByName[cc.name] = cc.portrait_url || null;
      if (cc.id) portraitById[cc.id] = cc.portrait_url || null;
    }
    const previewCharacters: PreviewCharacter[] = outline
      ? outline.characters.map((c) => ({
          id: c.id,
          name: c.name,
          description: c.description,
          fullbodyUrl: "/brand/logo-48.png",
          portraitUrl:
            portraitById[c.id] ?? portraitByName[c.name] ?? c.portrait_url ?? null,
          adjustments: [],
        }))
      : [];

    const previewScenes: PreviewScene[] = outline
      ? outline.scenes.map((s) => ({
          id: s.id,
          name: s.name,
          description: s.description_zh || s.description,
          userEdit: "",
        }))
      : [];

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
          charactersInScene: (s["characters_in_scene"] as string[]) || [],
        };
      });
    }

    // Best-effort BGM info
    let bgmUrl: string | null = null;
    try {
      const bgmInfo = await fetchBgmInfo(projectUuid, 1, token);
      if (bgmInfo.bgm_exists && bgmInfo.bgm_url) {
        bgmUrl = toAbsoluteUrl(bgmInfo.bgm_url);
      }
    } catch {
      // ignore — BGM is optional
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
    // 404 / 401 / network — let caller route to /create or /login as appropriate
    const msg = err instanceof Error ? err.message : "";
    const notFound = /404|不存在|not found/i.test(msg);
    return { hydratePayload: null, reconciledStage: urlStage, notFound };
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
  const [hydrating, setHydrating] = useState(!!urlProjectUuid);
  const [hydrateError, setHydrateError] = useState<string | null>(null);

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

    void (async () => {
      const result = await hydrateProjectFromBackend(urlProjectUuid, token, safeUrlStage);
      if (result.notFound) {
        setHydrateError("项目不存在或已删除");
        setHydrating(false);
        return;
      }
      if (!result.hydratePayload) {
        setHydrateError("加载项目失败，请刷新重试");
        setHydrating(false);
        return;
      }
      hydratedFor.current = urlProjectUuid;
      dispatch({ type: "HYDRATE_FROM_BACKEND", payload: result.hydratePayload });

      // If backend reconciled to a different stage than the URL says, redirect.
      if (result.reconciledStage !== safeUrlStage) {
        const newUrl = buildCreateUrl(urlProjectUuid, result.reconciledStage);
        if (newUrl) {
          lastPushedUrlRef.current = newUrl;
          router.replace(newUrl);
        }
      } else {
        lastPushedUrlRef.current = `/create/${urlProjectUuid}/${safeUrlStage}`;
      }
      setHydrating(false);
    })();
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
          </div>
        </main>
      </div>
    );
  }

  if (urlProjectUuid && hydrateError) {
    return (
      <div className="min-h-screen bg-bg-primary">
        <CreateHeader />
        <main className="container-lg py-8 pb-24">
          <div className="max-w-lg mx-auto text-center pt-20">
            <AlertCircle className="w-8 h-8 text-error mx-auto mb-3" />
            <p className="text-text-secondary text-sm mb-4">{hydrateError}</p>
            <button
              onClick={() => router.replace("/dashboard")}
              className="btn-primary px-8"
            >
              返回工作台
            </button>
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
