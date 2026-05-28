"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle2, AlertCircle, User, MapPin, ChevronRight, Pencil, Play, ImageOff, RefreshCw, ChevronDown, ChevronUp, RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCreate } from "@/contexts/CreateContext";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";
import { useStageLock } from "@/hooks/useStageLock";
import { useETA } from "@/hooks/useETA";
import { buildCreateUrl } from "@/lib/createUrl";
import { useToast } from "@/components/ui/Toast";
import { mockShotGenProgress, mockPreviewCharacters, mockPreviewScenes } from "@/lib/mock-data";
import type { PreviewCharacter, PreviewScene, Shot } from "@/types/create";

const ADJUST_TAGS = ["换发色", "换服装", "更年轻", "更成熟", "换风格"];

// TASK-FRONTEND-STALE-COPY: Stage-aware progress tip — copy changes as pipeline advances
// Stage groups:
//   Early (story_generation, character_design): tell user "confirm characters coming up"
//   Script (screenplay, storyboard): characters about to be confirmed, scripting in progress
//   Image (image_preparation, image_generation): characters confirmed, drawing now
//   BGM (bgm, music): final step
function getProgressTip(stage: string | null | undefined, subPhase: string): string | null {
  if (!stage && subPhase === "text-gen") {
    // Early text-gen before backend stage is known
    return "稍后需要你确认角色和场景哦～可以先喝杯可可，保持页面打开就好";
  }
  if (!stage) return null;
  if (stage === "story_generation" || stage === "character_design") {
    return "稍后需要你确认角色和场景哦～可以先喝杯可可，保持页面打开就好";
  }
  if (stage === "screenplay" || stage === "storyboard") {
    return "剧本和分镜马上准备好，角色确认结束后画面就开始了～";
  }
  if (stage === "image_preparation" || stage === "image_generation") {
    return "画面正在一张一张生成中，马上就能看到精彩成果！";
  }
  if (stage === "bgm" || stage === "music") {
    return "BGM 配乐处理中，最后一步啦，再等一小会儿～";
  }
  // character_ready is a transition point, not a waiting stage — no tip needed
  return null;
}

// RF-3: 19 carousel tips (9 original + 10 new, without cocoa)
const CAROUSEL_TIPS = [
  // Original product tips (4, cocoa removed)
  "你知道吗？序话支持 28 种视觉风格，从写实到水墨都有",
  "角色预览时，你可以调整角色的发色、服装和年龄",
  "场景已生成，请确认是否符合预期",
  "生成完成后，不满意的画面可以单独重新生成",
  // Original creative inspiration (5)
  "试试用一句话描述你最难忘的梦境",
  "古装武侠 + 水墨风格 = 国风绝配",
  "一个反转结局，往往比平铺直叙更打动人",
  "好的故事开头，从一个意想不到的场景开始",
  "短视频模式只需 4-10 张画面，很快就能出片",
  // New product tips (5)
  "生成完成后，可以一键导出所有画面打包下载",
  "同一个故事，换个风格就是完全不同的视觉体验",
  "你可以删除不需要的画面，只保留最精华的部分",
  "每个画面都可以单独编辑旁白文字",
  "中篇模式支持 36 张画面，能讲更完整的故事",
  // New creative inspiration (5)
  "把你最喜欢的电影情节用一句话描述出来试试",
  "悬疑故事 + 赛博朋克风格 = 视觉冲击",
  "从一个普通物件出发，让它成为故事的核心",
  "两个陌生人在意想不到的地方相遇——故事就此开始",
  "试试给角色加一个有趣的口头禅或习惯",
];

// RF-2: Filter out technical error details (SQL, tracebacks, etc.)
const friendlyError = (msg: string): string => {
  if (/sql|pymysql|traceback|exception|errno|operationalerror|dataerror|integrityerror/i.test(msg)) {
    return "生成遇到问题，请稍后重试";
  }
  return msg;
};

// UX-8: Replace "张图像" with "个片段" in any backend progress message
// Example: "已生成 12/18 张图像..." → "已生成 12/18 个片段..."
const friendlyMessage = (msg: string): string => {
  return msg.replace(/张图像/g, "个片段");
};

// UX-9 / FE-1: Map backend stage name → user-facing phase label. Covers all
// Pipeline stages (see pipeline_orchestrator.py progress_callback calls).
// TASK-T6-FIXBATCH: Added character_design (5-7%) and image_preparation (65-75%) per Agent A
const STAGE_LABEL: Record<string, string> = {
  story_generation: "正在生成故事大纲",
  character_design: "正在生成角色画像",    // Agent A 新加 stage (5-7%)
  character_ready: "角色设计完成",
  screenplay: "正在编写剧本",
  storyboard: "正在创建分镜",
  // T21-NEW-7 (2026-05-21 DEC-047 v1.4): Stage 4.5 场景参考图生成阶段文案
  scene_image_preparation: "正在准备场景视觉",
  scene_references_ready: "场景视觉已就绪",
  image_preparation: "正在准备画面",        // Agent A 新加 stage (65-75%)
  image_generation: "正在绘制画面",
  bgm: "正在生成配乐",
  music: "正在生成配乐",
  completed: "故事生成完成",
};

// UX-12: Sub-title copy varies by pipeline stage
// RISK-T15-1 fix: text-gen stages (story_generation → storyboard) no longer say
// "可以选择后台生成" — user cannot leave until both characters AND scenes are confirmed.
const STAGE_SUBTITLE: Record<string, string> = {
  story_generation: "AI 正在创作故事，请稍候",
  character_design: "AI 正在创作故事，请稍候",
  character_ready: "AI 正在创作故事，请稍候",
  screenplay: "AI 正在创作故事，请稍候",
  storyboard: "AI 正在创作故事，请稍候",
  // T21-NEW-7 v1.4: Stage 4.5 不允许 "后台生成" — 用户即将进入 R4-3 确认点
  scene_image_preparation: "AI 正在准备场景视觉，稍后请确认",
  scene_references_ready: "场景视觉已就绪，请确认",
  image_preparation: "AI 正在逐张绘制画面，可以选择后台生成",
  image_generation: "AI 正在逐张绘制画面，可以选择后台生成",
  bgm: "AI 正在生成配乐，可以选择后台生成",
  music: "AI 正在生成配乐，可以选择后台生成",
};

function resolveSubtitle(stage: string | null | undefined): string {
  if (stage && STAGE_SUBTITLE[stage]) return STAGE_SUBTITLE[stage];
  // Default: show text-gen subtitle for early/unknown stages
  // RISK-T15-1 fix: default fallback also updated to "请稍候"
  return "AI 正在创作故事，请稍候";
}

function resolvePhaseTitle(isError: boolean, subPhase: string, stage: string | null | undefined): string {
  if (isError) return "生成遇到问题";
  // P2-4: stage='completed' → show completion title directly (no "即将完成" branch)
  if (stage === "completed") return STAGE_LABEL.completed;
  // UX-9: Prefer backend stage when available — never cache, always re-map
  if (stage && STAGE_LABEL[stage]) return STAGE_LABEL[stage];
  if (subPhase === "shot-gen") return "正在绘制画面";
  return "正在创作你的故事";
}

export default function StageC() {
  const { state, dispatch } = useCreate();
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const cancelRef = useRef<(() => void) | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedRef = useRef(false); // R5-1: prevent repeated completed branch execution
  // RISK-T18-G: guard against duplicate /story fetches when character_ready triggers.
  // The 2s text-gen poller can fire multiple ticks before clearPoll() stops the interval
  // (React StrictMode double-invoke, or interval already queued). Without this guard,
  // each tick independently fetches /story → 41 HTTP_ERROR 404 storm in client.log.
  const charPreviewFetchingRef = useRef(false);
  // BUG-PROGRESS-LIST-SKIP-SHOT: ref to access latest generationLog inside polling interval
  // without adding generationLog as a dependency (which would restart the interval)
  const generationLogRef = useRef(state.generationLog);

  // BUG-PROGRESS-LIST-SKIP-SHOT: keep generationLogRef in sync so polling interval can access
  // latest log entries without generationLog as a dependency
  generationLogRef.current = state.generationLog;

  // BUG-T13-* fix: refs for state values read inside poller closures.
  // Without these, the poller setInterval captures stale values at useEffect setup time.
  // E.g. state.charactersConfirmed at character_ready guard would be the value from when
  // text-gen useEffect first ran, even if user has now confirmed.
  const charactersConfirmedRef = useRef(state.charactersConfirmed);
  charactersConfirmedRef.current = state.charactersConfirmed;

  // RISK-T19-3: Live ref tracking current generationProgress so the text-gen effect
  // can check current progress (not mount-time snapshot) when deciding whether to
  // dispatch START_GENERATION. Without this, transitioning subPhase from "shot-gen"
  // back to "text-gen" (via the Watcher's storyboard_running → "text-gen" mapping)
  // would trigger START_GENERATION (because initialProgressRef.current = 0 from mount)
  // and reset generationProgress to 0% even though the backend is already at 37-62%.
  const generationProgressRef = useRef(state.generationProgress);
  generationProgressRef.current = state.generationProgress;

  // [StageC] Log #1 — subPhase + currentStage changes (covers B26/B27: why are we on which screen)
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.log("[StageC] subPhase changed:", state.generationSubPhase, "currentStage:", state.currentStage, "URL:", typeof window !== "undefined" ? window.location.pathname : "(ssr)");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.generationSubPhase, state.currentStage]);

  // F-1: Carousel tip state — random start index
  const [tipIndex, setTipIndex] = useState(() => Math.floor(Math.random() * CAROUSEL_TIPS.length));

  // F-2: Start time ref for time estimation
  const startTimeRef = useRef<number>(Date.now());

  // RF-4: Backend estimated remaining seconds — consumed by useETA hook
  // (retained as a ref so poller closures can write to it without causing re-renders)
  const backendEstimatedSecondsRef = useRef<number | null>(null);

  // RISK-NEW-1: Backend actual elapsed seconds — consumed by useETA hook for sanity check
  // Written by both text-gen and shot-gen pollers; read by useETA via actualElapsedSec param.
  const backendActualElapsedSecRef = useRef<number | null>(null);

  // T20-9.v3: Shot count fields from STATUS_API_CONTRACT v1.1 §1.2.
  // Written by shot-gen poller; read by useETA hook for frontend fallback ETA formula.
  // Retained as refs (not state) to avoid re-render on every poll tick.
  const backendShotsTotalRef = useRef<number | null>(null);
  const backendShotsCompletedRef = useRef<number | null>(null);
  const backendShotsFailedRef = useRef<number | null>(null);

  // Wave 9 / DEC-030 顺解 RISK-T15-7: Track the last seen backend stage so that
  // when stage transitions (e.g. screenplay → storyboard → image_preparation),
  // we RESET lastEtaSecondsRef. Without reset the UX-7 monotonicity guard would
  // compress every new stage's ETA into the tiny tail of the previous stage,
  // showing "1 min" while the next stage actually needs 5-6 min (Founder test15
  // observed this — backend ETA=350s but UI showed 1 min).
  //
  // Reset semantics: lastEtaSecondsRef = null lets the next ETA poll be accepted
  // verbatim (no clamp). Subsequent polls within the same stage resume monotonic.
  const lastStageRef = useRef<string | null>(null);

  // F-2 (R3): Simulated early progress ref — advances 1% per 12s up to 5%, prevents "0% stuck" perception
  const simulatedProgressRef = useRef(0);
  const simulatedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // F-3: Consecutive error counters for both polling effects
  const textGenErrorCount = useRef(0);
  const shotGenErrorCount = useRef(0);
  const [showRetryHint, setShowRetryHint] = useState(false);
  // RISK-T16-3: distinguish network outage from true pipeline failure.
  // When online event fires, reset error counters so pollers resume normally.
  const [networkOffline, setNetworkOffline] = useState(false);

  // FE-1: Track current backend stage for precise phase title mapping
  const [currentStage, setCurrentStage] = useState<string | null>(null);

  // RISK-T19-2 / RISK-T17-8: Failed UI friendly state
  // - showTechDetails: whether the collapsible "技术详情" section is expanded
  // - restartLoading: whether the "原地重启" API call is in-flight
  // - restartError: error message if restart call failed (null = no error yet)
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [restartLoading, setRestartLoading] = useState(false);
  const [restartError, setRestartError] = useState<string | null>(null);

  const token = getStoredToken();
  const projectId = state.projectId;
  const useRealApi = !!(isLoggedIn && token && projectId);

  const clearPoll = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  // RISK-T16-3: Listen for browser "online" event — when network recovers,
  // reset error counters so pollers resume and hide the network-offline banner.
  // The pollers themselves (setInterval) keep running during offline; they will
  // throw fetch errors which increment counters. On "online", we reset counters
  // so the next successful poll clears the retry hint naturally.
  useEffect(() => {
    const handleOnline = () => {
      // eslint-disable-next-line no-console
      console.log("[StageC] RISK-T16-3: network online event — resetting error counters, resuming polls");
      textGenErrorCount.current = 0;
      shotGenErrorCount.current = 0;
      setNetworkOffline(false);
      setShowRetryHint(false);
    };
    const handleOffline = () => {
      // eslint-disable-next-line no-console
      console.log("[StageC] RISK-T16-3: network offline event — setting networkOffline=true");
      setNetworkOffline(true);
      setShowRetryHint(true);
    };
    if (typeof window !== "undefined") {
      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      }
    };
  }, []); // intentionally empty — event listeners don't depend on React state

  // F-1: Carousel timer — 8 second rotation
  // P2-4: Stop rotation when progress >= 100 or stage is completed
  useEffect(() => {
    const isCompleted = state.generationProgress >= 100 || currentStage === "completed";
    const isGenerating = (state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen")
      && state.generationStatus !== "error"
      && !isCompleted;
    if (!isGenerating) return;

    const interval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % CAROUSEL_TIPS.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [state.generationSubPhase, state.generationStatus, state.generationProgress, currentStage]);

  // F-2: Reset start time when entering a new generation sub-phase
  useEffect(() => {
    if (state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen") {
      startTimeRef.current = Date.now();
    }
  }, [state.generationSubPhase]);

  // Wave 9 / DEC-030 顺解 RISK-T15-7: Keep tracking last stage for logging / debug purposes.
  // Stage-based ETA reset is now handled inside useETA hook (stage change useEffect).
  useEffect(() => {
    if (lastStageRef.current && currentStage && lastStageRef.current !== currentStage) {
      // eslint-disable-next-line no-console
      console.log(
        "[StageC] Wave9: stage transition",
        lastStageRef.current,
        "→",
        currentStage,
        "— useETA hook handles ETA reset internally (RISK-T17-5)",
      );
    }
    lastStageRef.current = currentStage ?? null;
  }, [currentStage]);

  // Wave 11.3 / RISK-T17-5: useETA hook replaces the old estimatedMinutes IIFE.
  // T20-9.v3 (Wave 17): Pass shots_total / shots_completed for frontend fallback ETA formula.
  //   Priority chain: estimatedRemainingSeconds > shots formula > backendEtaSec > budget fallback.
  //   "正在收尾" removed — progress >= 95% now shows concrete ETA number (Founder feedback fix).
  const { etaText } = useETA({
    stage: currentStage,
    progress: state.generationProgress,
    estimatedRemainingSeconds: backendEstimatedSecondsRef.current,  // T20-9: top priority
    shotsTotal: backendShotsTotalRef.current,                       // T20-9.v3: fallback formula
    shotsCompleted: backendShotsCompletedRef.current,               // T20-9.v3: fallback formula
    shotsFailed: backendShotsFailedRef.current,                     // T20-9.v3: display only
    backendEtaSec: backendEstimatedSecondsRef.current,              // legacy fallback (backward compat)
    actualElapsedSec: backendActualElapsedSecRef.current,           // RISK-NEW-1: ignored
  });

  // P2-2: Removed stale checkpointPreview logic (L209-214).
  // Character preview is now triggered by character_ready stage event, not progress thresholds.

  useEffect(() => { return () => clearPoll(); }, [clearPoll]);

  // RISK-T19-3: initialProgressRef (D.13 mount-time snapshot) was replaced by
  // generationProgressRef (live ref, kept in sync each render — declared above near
  // charactersConfirmedRef). Using the live ref prevents START_GENERATION from resetting
  // progress to 0% when the Watcher transitions subPhase back to "text-gen" during storyboard.

  // D.23: Lifted completion handler — callable from both text-gen poller and shot-gen poller.
  // Single guard (completedRef) prevents double-execution regardless of which phase triggers it.
  const finalizeAndGoToPreview = useCallback(async () => {
    if (completedRef.current) return;
    completedRef.current = true;
    clearPoll();
    // eslint-disable-next-line no-console
    console.time("[FE-5] /generation-result roundtrip");
    try {
      const result = await apiFetch<{
        storyboard: { shots: Array<{
          shotId: number;
          imageUrl: string | null;
          image_url_thumb?: string | null;
          narration?: string;
          narrationSegment?: string;
          textOverlay?: { type: string; text: string };
          shotType?: string;
          cameraAngle?: string;
          sceneId?: number;
          // B44: safety_advice is structured object (or null) when content_safety_failure
          safety_advice?: { suspected_terms: string[]; suggested_changes: { original: string; suggestion: string }[]; user_message: string } | null;
          error_message?: string | null;
        }> } | null;
        totalShots: number;
      }>(`/projects/${projectId}/generation-result`, {}, token);
      // eslint-disable-next-line no-console
      console.timeEnd("[FE-5] /generation-result roundtrip");

      if (result.storyboard?.shots?.length) {
        // Task#13 fix: /generation-result backend currently returns imageUrl as
        // /api/projects/{uuid}/images/shot_XX.png (old route that returns 404 on VPS).
        // Normalise to /static/outputs/{uuid}/images/shot_XX.png so toAbsoluteUrl
        // produces the correct CDN-cached static URL.
        const fixImageUrl = (url: string | null): string | null => {
          if (!url) return null;
          const m = url.match(/^\/api\/projects\/([^/]+)\/images\/(.+)$/);
          if (m) return `/static/outputs/${m[1]}/images/${m[2]}`;
          return url;
        };
        const mappedShots: Shot[] = result.storyboard.shots.map((s) => ({
          shotId: s.shotId,
          sceneId: s.sceneId || 1,
          imagePrompt: "",
          narrationSegment: s.narrationSegment || s.narration || "",
          shotType: s.shotType || "medium shot",
          cameraAngle: s.cameraAngle || "eye level",
          textType: s.textOverlay?.type || "narration",
          chineseText: s.textOverlay?.text ? [s.textOverlay.text] : [],
          imageUrl: toAbsoluteUrl(fixImageUrl(s.imageUrl)),
          imageUrlThumb: toAbsoluteUrl(fixImageUrl(s.image_url_thumb ?? null)),
          charactersInScene: [],
          // D.17: content safety fields
          safetyAdvice: s.safety_advice || null,
          errorMessage: s.error_message || null,
        }));
        dispatch({ type: "GENERATION_COMPLETE", payload: mappedShots });
      } else {
        dispatch({ type: "GENERATION_COMPLETE", payload: [] });
      }
      dispatch({ type: "SET_STAGE", payload: "preview" });

      // RISK-T14-12: Browser Notification when generation completes (user may have gone to dashboard).
      // Only fire if page is NOT currently visible (user is elsewhere) to avoid intrusive popup.
      if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
        if (document.visibilityState !== "visible") {
          const title = state.outline?.title || "故事";
          new Notification("序话Story", {
            body: `《${title}》生成完成 — 点击查看`,
            icon: "/brand/logo-40.png",
          });
        }
      }
    } catch {
      // eslint-disable-next-line no-console
      console.timeEnd("[FE-5] /generation-result roundtrip");
      dispatch({ type: "GENERATION_ERROR", payload: "加载生成结果失败" });
    }
  }, [projectId, token, dispatch, clearPoll, state.outline]);

  // D.23: Completion watcher for char-preview and scene-refs-preview subphases.
  // When the user is at the character or scene refs confirmation checkpoint, no other poller
  // is running. If the backend pipeline completes (skipped or fast-tracked) while the
  // user is on that checkpoint, we need to detect it and auto-redirect to /preview.
  // Poll every 5s (less aggressive than 2s since these are user checkpoints, not waiting screens).
  // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene-preview 从 isAtCheckpoint 条件中移除.
  useEffect(() => {
    // T21-NEW-7 (2026-05-21 DEC-047 v1.4): scene-refs-preview 也是用户停留 checkpoint,
    //   D.23 watcher 同样需要监控 — 如果 R4-3 等待期间 pipeline 完成 (1800s 超时) 或失败,
    //   要正确触发 finalize / error UI.
    const isAtCheckpoint =
      state.generationSubPhase === "char-preview" ||
      state.generationSubPhase === "scene-refs-preview";
    if (!isAtCheckpoint || !useRealApi) return;

    // Reset completion guard so this watcher can trigger finalizeAndGoToPreview
    completedRef.current = false;

    const watchInterval = setInterval(async () => {
      try {
        // Wave 9 / DEC-030: status response now includes ui_phase + hydrate_hints +
        // characters_confirmed + scenes_confirmed. We type with optional fields for
        // backward compat with pre-Wave-9 backend.
        const status = await apiFetch<{
          status: string;
          stage: string | null;
          progress: number;
          message: string;
          ui_phase?: string | null;
        }>(`/projects/${projectId}/chapters/1/status`, {}, token, { silentStatuses: [404] });
        // D.23 / Wave 9: prefer ui_phase=completed over legacy triad check
        const isCompleted =
          status.ui_phase === "completed" ||
          status.status === "completed" ||
          status.stage === "completed" ||
          status.progress >= 100;
        if (isCompleted) {
          clearInterval(watchInterval);
          console.info("[D.23 / Wave9] pipeline completed while at checkpoint — auto-redirecting to preview");
          await finalizeAndGoToPreview();
        }
        if (status.status === "failed") {
          clearInterval(watchInterval);
          dispatch({ type: "GENERATION_ERROR", payload: status.message || "生成失败" });
        }
      } catch {
        // Non-fatal: ignore poll errors at checkpoints, user can still manually confirm
      }
    }, 5000);

    return () => clearInterval(watchInterval);
  }, [state.generationSubPhase, useRealApi, projectId, token, dispatch, finalizeAndGoToPreview]);

  // ============ Text-gen phase ============
  useEffect(() => {
    if (state.generationSubPhase !== "text-gen") return;
    // RISK-T19-3: Use generationProgressRef.current (live ref, kept in sync each render)
    // instead of initialProgressRef.current (mount-time snapshot) to decide whether to
    // dispatch START_GENERATION.
    //
    // D.13 original: "if hydrated from backend (F5/deep-link), progress > 0 — skip reset"
    // ↳ Still works: hydration sets generationProgress > 0 → generationProgressRef.current > 0 → skip.
    //
    // RISK-T19-3 new: "if watcher transitions subPhase shot-gen → text-gen during storyboard,
    //   progress may already be 37-62% from shot-gen poller — skip reset"
    // ↳ initialProgressRef.current was 0 at StageC mount → START_GENERATION was incorrectly
    //   dispatched → progress reset to 0% → user saw 0% for 6 min despite backend at 60%+.
    // ↳ Fix: use live generationProgressRef.current > 0 → skip when any real progress exists.
    //
    // We do NOT add state.generationProgress to deps to avoid restarting poller on every tick.
    if (generationProgressRef.current > 0) {
      // Already has real progress (hydrated OR transitioning from shot-gen during storyboard)
      // — skip reset, polling below will continue from real progress
    } else {
      dispatch({ type: "START_GENERATION" });
    }

    if (!useRealApi) {
      // Mock path
      let cancelled = false;
      const steps = [
        { progress: 10, message: "正在构思故事大纲...", delay: 800 },
        { progress: 25, message: "正在设计角色外貌...", delay: 1200 },
        { progress: 45, message: "正在编写分场剧本...", delay: 1500 },
        { progress: 65, message: "正在绘制分镜脚本...", delay: 1200 },
        { progress: 80, message: "正在生成角色参考图...", delay: 1000 },
        { progress: 90, message: "角色参考图生成完成", delay: 500 },
      ];
      let i = 0;
      const run = () => {
        if (cancelled || i >= steps.length) {
          if (!cancelled) {
            dispatch({ type: "SET_PREVIEW_CHARACTERS", payload: mockPreviewCharacters });
            dispatch({ type: "SET_PREVIEW_SCENES", payload: mockPreviewScenes });
            dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "char-preview" });
          }
          return;
        }
        setTimeout(() => {
          if (!cancelled) {
            dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: steps[i].progress, message: steps[i].message } });
            i++;
            run();
          }
        }, steps[i].delay);
      };
      run();
      return () => { cancelled = true; };
    }

    // Real API: poll job status
    textGenErrorCount.current = 0;

    // F-2 (R3): Start simulated early progress — 1% per 12 seconds, caps at 5%
    simulatedProgressRef.current = 0;
    if (simulatedTimerRef.current) clearInterval(simulatedTimerRef.current);
    simulatedTimerRef.current = setInterval(() => {
      if (simulatedProgressRef.current < 5) {
        simulatedProgressRef.current += 1;
        // Dispatch simulated progress if real progress hasn't caught up yet
        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: simulatedProgressRef.current, message: "正在启动创作引擎..." } });
      }
    }, 12000);

    // RISK-T20-24 (Wave 4): Extract poll body into a named function so we can fire
    // it once immediately on mount AND every 2s via setInterval. This eliminates the
    // "0% stuck for first 2s" bug Founder observed during Stage 2 early (backend at
    // progress=5-10% but frontend at 0% until first poll fires).
    const runTextGenPoll = async () => {
      try {
        // Wave 9 / DEC-030: status response now includes ui_phase + hydrate_hints +
        // confirmed flags. Type with optional fields for backward compat.
        const status = await apiFetch<{
          status: string;
          stage: string;
          progress: number;
          message: string;
          estimated_remaining_seconds?: number | null;  // T20-44: null allowed (contract v1.3)
          actual_elapsed_sec?: number | null;  // RISK-NEW-1
          ui_phase?: string | null;
          hydrate_hints?: { endpoint: string; display_field: string; expected_data_shape: string } | null;
          characters_confirmed?: boolean;
          scenes_confirmed?: boolean;
        }>(`/projects/${projectId}/chapters/1/status`, {}, token, { silentStatuses: [404] });
        textGenErrorCount.current = 0; // F-3 / RISK-T16-3: reset on success
        setShowRetryHint(false);
        setNetworkOffline(false); // RISK-T16-3: clear network-offline banner on successful poll

        // FE-1: capture backend stage for title mapping
        // Note: setCurrentStage triggers the lastStageRef useEffect (above) which resets
        // lastEtaSecondsRef on stage change — Wave 9 顺解 RISK-T15-7.
        if (status.stage) setCurrentStage(status.stage);

        // RF-4: Store backend estimated remaining seconds.
        // T20-44: Use >= 0 (consistent with shot-gen poller) — zero = "almost done" is valid.
        // STATUS_API_CONTRACT v1.3 §1.4: Backend authoritative ETA, read directly.
        if (typeof status.estimated_remaining_seconds === "number" && status.estimated_remaining_seconds >= 0) {
          backendEstimatedSecondsRef.current = status.estimated_remaining_seconds;
        } else {
          backendEstimatedSecondsRef.current = null;
        }
        // RISK-NEW-1: Store actual elapsed seconds for useETA sanity check
        backendActualElapsedSecRef.current =
          typeof status.actual_elapsed_sec === "number" ? status.actual_elapsed_sec : null;

        // FE-3: Trust real backend progress once any value > 0 comes in. Only use
        // the simulated value when backend is still at 0 (early startup).
        const effectiveProgress = status.progress > 0 ? status.progress : simulatedProgressRef.current;
        // Once real progress exceeds 5%, stop the simulated timer
        if (status.progress >= 5 && simulatedTimerRef.current) {
          clearInterval(simulatedTimerRef.current);
          simulatedTimerRef.current = null;
        }

        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: effectiveProgress, message: status.message } });

        // D.23 / Wave 9: If pipeline already completed (e.g. user refreshed mid-generation), skip
        // char-preview entirely and go straight to /preview.
        const isCompleted =
          status.ui_phase === "completed" ||
          status.status === "completed" ||
          status.stage === "completed" ||
          status.progress >= 100;
        if (isCompleted) {
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          await finalizeAndGoToPreview();
          return;
        }

        // RF-6 / Wave 9 顺解 T15-8: Transition to char-preview when backend ui_phase is
        // "char_review" (preferred — authoritative) OR stage is "character_ready" (legacy fallback).
        // Wave 9 ui_phase already incorporates project.characters_confirmed (backend logic),
        // so when ui_phase=char_review we KNOW user hasn't yet confirmed.
        const shouldShowCharPreview =
          status.ui_phase === "char_review" ||
          status.stage === "character_ready";
        if (shouldShowCharPreview) {
          // B49-followup: BUG-URL-PINGPONG — if characters already confirmed, do NOT revert
          // to char-preview. Without this guard, the text-gen poller keeps dispatching
          // "char-preview" every 2s while backend stage remains "character_ready" (it persists
          // until Stage 3 starts). This caused URL to loop: /scenes → /characters → /generating → /characters
          //
          // BUG-T13-URL-PINGPONG-V2 fix: read from ref to avoid stale closure.
          // Previously read state.charactersConfirmed which was captured at useEffect setup
          // and could lag behind real confirms during a long-running poll session.
          if (charactersConfirmedRef.current) {
            // eslint-disable-next-line no-console
            console.log("[StageC] character_ready but charactersConfirmed=true (ref), skipping char-preview re-entry");
            return; // continue polling until stage advances
          }
          // RISK-T18-G: prevent duplicate /story fetch when multiple poller ticks fire before
          // clearPoll() stops the interval. charPreviewFetchingRef is set true on first entry
          // and reset to false after dispatch (or if text-gen useEffect remounts).
          if (charPreviewFetchingRef.current) {
            // eslint-disable-next-line no-console
            console.log("[StageC] RISK-T18-G: char-preview fetch already in progress — skipping duplicate /story fetch");
            return;
          }
          charPreviewFetchingRef.current = true;
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }

          // P0-3: portrait_url lives in chapter.characters_json (not outline.characters).
          // Fetch /chapters/1/story to get real portrait_url values.
          // Agent A P1-5 ensures character_ready fires only after all portraits are ready.
          // D.21: /chapters/1/story returns 400 when chapter.status is "pending"/"generating_story"
          // (chapter has characters_json but full_script not yet written). Catch 400 same as 404.
          let chapterCharacters: Array<{ id?: string; name: string; portrait_url?: string | null }> = [];
          if (projectId && token) {
            try {
              const storyResp = await apiFetch<{
                characters: Array<{ id?: string; name: string; portrait_url?: string | null }>;
              // RISK-T18-G: 400/404 are routine before story_ready stage — suppress warn in client-log proxy.
              }>(`/projects/${projectId}/chapters/1/story`, {}, token, { silentStatuses: [400, 404] });
              chapterCharacters = storyResp.characters || [];
            } catch (storyErr) {
              // D.21: Non-fatal — 400 means chapter not yet in story_ready state (still generating).
              // 404 means chapter doesn't exist yet. Both are routine at character_ready stage.
              console.warn("[StageC] /chapters/1/story fetch failed (routine):", storyErr instanceof Error ? storyErr.message : storyErr);
            }
          }

          // Build portrait lookup from chapter API response
          const portraitByName: Record<string, string | null> = {};
          for (const cc of chapterCharacters) {
            if (cc.name) portraitByName[cc.name] = cc.portrait_url || null;
            if (cc.id) portraitByName[cc.id] = cc.portrait_url || null;
          }

          // D.21: Static portrait URL fallback — when /chapters/1/story returns 400/404,
          // chapterCharacters is empty and portraitByName has no entries.
          // Backend writes portrait files to: /static/outputs/{projectId}/character_refs/{char_id}_portrait.png
          // char_id comes from confirmed_outline.characters[i].id = "char_001", "char_002", etc.
          // We can construct the URL directly and let the browser verify (404 → img onError → no-op).
          const buildStaticPortraitUrl = (charId: string | null | undefined): string | null => {
            if (!charId || !projectId) return null;
            // Only construct URL for known char_XXX id format (backend convention)
            if (!/^char_\d+/.test(charId)) return null;
            return `/static/outputs/${projectId}/character_refs/${charId}_portrait.png`;
          };

          // [D.21] Log #2 — portrait fallback chain: how many chars from story API vs static fallback
          // eslint-disable-next-line no-console
          console.log("[D.21] character_ready: chapterCharacters from /story API:", chapterCharacters.length, "portraitByName keys:", Object.keys(portraitByName));

          // UX-1: Use real outline data for character/scene previews,
          // with portrait_url fetched from chapter.characters_json.
          const chars: PreviewCharacter[] = state.outline?.characters?.map(c => {
            // [D.21] Log #3 — per-character portrait resolution
            // eslint-disable-next-line no-console
            console.log("[D.21] resolvePortraitForCharacter charId=", c.id, "name=", c.name);
            const apiPortraitUrl = portraitByName[c.id] ?? portraitByName[c.name] ?? null;
            // eslint-disable-next-line no-console
            console.log("[D.21] step 1 - API portrait_url:", apiPortraitUrl ?? "(empty)");
            const staticUrl = buildStaticPortraitUrl(c.id);
            // eslint-disable-next-line no-console
            console.log("[D.21] step 2 - buildStaticPortraitUrl:", staticUrl ?? "(null — charId not char_XXX format or projectId missing)");
            const outlineUrl = c.portrait_url ?? null;
            // eslint-disable-next-line no-console
            console.log("[D.21] step 3 - outline portrait_url:", outlineUrl ?? "(empty)");
            const finalUrl = apiPortraitUrl ?? staticUrl ?? outlineUrl ?? null;
            // eslint-disable-next-line no-console
            console.log("[D.21] FINAL portrait src for", c.id, ":", finalUrl ?? "(NULL — will not render!)");
            return {
              id: c.id, name: c.name, description: c.description,
              fullbodyUrl: "/brand/logo-48.png",
              // P0-3 / D.21: prefer chapter portrait (from /story API) → static URL fallback (when story returns 400) → outline portrait → null
              portraitUrl: finalUrl,
              adjustments: [],
            };
          }) || mockPreviewCharacters;
          // F-3 (R3): Prefer description_zh (Chinese) if available, fallback to description (English)
          const scenes: PreviewScene[] = state.outline?.scenes?.map(s => ({
            id: s.id, name: s.name, description: s.description_zh || s.description, userEdit: "",
          })) || mockPreviewScenes;
          dispatch({ type: "SET_PREVIEW_CHARACTERS", payload: chars });
          dispatch({ type: "SET_PREVIEW_SCENES", payload: scenes });
          dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "char-preview" });
          // RISK-T18-G: reset guard after successful dispatch so that if StageC re-mounts
          // (e.g. hot reload or React StrictMode re-mount), the next text-gen cycle can
          // correctly re-enter the char-preview path.
          charPreviewFetchingRef.current = false;
        }

        if (status.status === "failed") {
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          dispatch({ type: "GENERATION_ERROR", payload: status.message || "生成失败" });
        }
      } catch (fetchErr) {
        // RISK-T16-3 / F-3: Consecutive error handling.
        // Distinguish network outage (navigator.onLine=false, or TypeError "Failed to fetch")
        // from true server errors. Network errors increment counter but do NOT immediately
        // show the fatal error page — instead show "网络连接中断，正在重试..." banner and
        // let the poller keep retrying. Only true backend failures (status=failed) trigger
        // the error page (handled above in the success branch).
        textGenErrorCount.current++;
        const isNetworkError =
          (typeof window !== "undefined" && !window.navigator.onLine) ||
          (fetchErr instanceof TypeError && /failed to fetch|network/i.test(fetchErr.message));
        if (isNetworkError) {
          setNetworkOffline(true);
          setShowRetryHint(true);
        } else if (textGenErrorCount.current >= 3) {
          setShowRetryHint(true);
        }
        // Only fatal after 15+ consecutive non-network errors (server truly unreachable).
        // For network errors, keep retrying until "online" event resets the counter.
        if (textGenErrorCount.current >= 15 && !isNetworkError) {
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          dispatch({ type: "GENERATION_ERROR", payload: "服务器连接异常，请稍后刷新页面重试" });
        }
      }
    };

    // RISK-T20-24 (Wave 4): Fire poll once immediately on mount so progress bar
    // shows real backend value (e.g. Stage 2 progress=5) within ~200ms instead of
    // waiting 2s for first setInterval tick. Fixes "0% stuck 2s on entry to /generating".
    void runTextGenPoll();
    pollRef.current = setInterval(runTextGenPoll, 2000);

    return () => {
      clearPoll();
      if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
      // RISK-T18-G: reset charPreviewFetchingRef so that if the text-gen effect re-mounts
      // (e.g. due to subPhase dep change), the next cycle is not permanently blocked.
      charPreviewFetchingRef.current = false;
    };
  }, [state.generationSubPhase, dispatch, useRealApi, token, projectId, state.outline, clearPoll, finalizeAndGoToPreview]);

  // ============ Shot-gen phase ============
  useEffect(() => {
    if (state.generationSubPhase !== "shot-gen") return;
    // RF-1: Use CONTINUE_GENERATION to avoid resetting progress from 65% back to 0%
    dispatch({ type: "CONTINUE_GENERATION" });

    if (!useRealApi) {
      // Mock path
      const cancel = mockShotGenProgress(
        (progress, message) => {
          dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress, message } });
        },
        (shots) => {
          dispatch({ type: "GENERATION_COMPLETE", payload: shots });
          dispatch({ type: "SET_STAGE", payload: "preview" });
        }
      );
      cancelRef.current = cancel;
      return () => cancel();
    }

    // Real API: poll until completed
    shotGenErrorCount.current = 0;
    // FE-5: Reset completion guard on fresh entry into shot-gen. Without this,
    // if the ref leaked `true` from a previous mount / StrictMode double-invoke,
    // all subsequent completion ticks would `return` early and the user would
    // be stuck on "100%" with no preview transition.
    // D.23: completedRef is now shared with the lifted finalizeAndGoToPreview callback.
    completedRef.current = false;

    // RISK-T20-24 (Wave 4): Same first-poll-immediate pattern as text-gen poller.
    // When subPhase transitions to shot-gen, fire once on mount so progress bar
    // reflects backend state without 2s delay.
    const runShotGenPoll = async () => {
      try {
        // Wave 9 / DEC-030: shot-gen poller also reads ui_phase for completion check.
        // T20-9.v3: Added shots_total / shots_completed / shots_failed (STATUS_API_CONTRACT v1.1 §1.2).
        const status = await apiFetch<{
          status: string;
          stage: string;
          progress: number;
          message: string;
          estimated_remaining_seconds?: number | null;
          actual_elapsed_sec?: number | null;  // RISK-NEW-1
          ui_phase?: string | null;
          failed_shot_count?: number;
          partial_failure?: boolean;
          // STATUS_API_CONTRACT v1.1 §1.2: new shot count fields (T20-13 backend landed)
          shots_total?: number | null;
          shots_completed?: number | null;
          shots_failed?: number | null;
        }>(`/projects/${projectId}/chapters/1/status`, {}, token, { silentStatuses: [404] });
        shotGenErrorCount.current = 0; // F-3 / RISK-T16-3: reset on success
        setShowRetryHint(false);
        setNetworkOffline(false); // RISK-T16-3: clear network-offline banner on successful poll

        // FE-1: capture backend stage for title mapping
        // Note: setCurrentStage triggers the lastStageRef useEffect (above) which resets
        // lastEtaSecondsRef on stage change — Wave 9 顺解 RISK-T15-7.
        if (status.stage) setCurrentStage(status.stage);

        // RF-4: Store backend estimated remaining seconds.
        // T20-9.v3: Accept >= 0 (estimatedRemainingSeconds contract allows zero = "almost done").
        if (typeof status.estimated_remaining_seconds === "number" && status.estimated_remaining_seconds >= 0) {
          backendEstimatedSecondsRef.current = status.estimated_remaining_seconds;
        } else {
          backendEstimatedSecondsRef.current = null;
        }
        // RISK-NEW-1: Store actual elapsed seconds for useETA sanity check
        backendActualElapsedSecRef.current =
          typeof status.actual_elapsed_sec === "number" ? status.actual_elapsed_sec : null;

        // T20-9.v3: Store shots_total / shots_completed / shots_failed (STATUS_API_CONTRACT v1.1).
        // These replace the "已生成 X/Y" regex parse for ETA computation — backend now provides
        // the counts directly, no string parsing needed.
        backendShotsTotalRef.current =
          typeof status.shots_total === "number" ? status.shots_total : null;
        backendShotsCompletedRef.current =
          typeof status.shots_completed === "number" ? status.shots_completed : null;
        backendShotsFailedRef.current =
          typeof status.shots_failed === "number" ? status.shots_failed : null;

        // FE-3: Trust backend progress directly in shot-gen (no simulated clamp)
        // BUG-PROGRESS-LIST-SKIP-SHOT: When two shots complete within the same 2s polling window,
        // the backend stage_message only stores the latest one (single-field overwrite).
        // T20-9.v3: Use shots_completed (from STATUS_API_CONTRACT v1.1) instead of message regex.
        // If shots_completed jumped by more than 1 since last log entry, synthesize the intermediate
        // "已生成 N/M" entries so the UI shows a continuous log without gaps.
        //
        // T20-44: STATUS_API_CONTRACT v1.3 §1.4 — during bgm/postprocess/finalize/completed stages,
        // shots_completed == shots_total means "all shots processed, NOT still generating".
        // Skip log synthesis in these post-image-gen stages to avoid showing stale "已生成 N/N" entries
        // when the pipeline has moved on to BGM/finalization.
        const POST_IMAGE_GEN_STAGES = new Set(["bgm", "postprocess", "finalize", "completed"]);
        const isPostImageGen = POST_IMAGE_GEN_STAGES.has(status.stage);
        const latestCompleted = backendShotsCompletedRef.current;
        const totalShots = backendShotsTotalRef.current;
        if (!isPostImageGen && latestCompleted !== null && totalShots !== null && latestCompleted > 0) {
          // Find the last shot number we already showed in the log
          let lastKnownShot = 0;
          for (const entry of generationLogRef.current) {
            const m = entry.message?.match(/已生成\s*(\d+)\/(\d+)\s*个片段/);
            if (m) lastKnownShot = Math.max(lastKnownShot, parseInt(m[1], 10));
          }
          // Synthesize any missing intermediate entries
          for (let shot = lastKnownShot + 1; shot < latestCompleted; shot++) {
            dispatch({
              type: "UPDATE_GENERATION_PROGRESS",
              payload: { progress: status.progress, message: `已生成 ${shot}/${totalShots} 个片段...` },
            });
          }
        }
        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: status.progress, message: status.message } });

        // UX-11 / FE-5 / Wave 9: Broaden completion trigger. Detect any of:
        //   1. status.ui_phase === "completed" (Wave 9 authoritative)
        //   2. status.status === "completed"
        //   3. status.stage === "completed" (backend sets this after Stage 6 BGM done)
        //   4. status.progress >= 100
        // Trigger immediately — do NOT wait for next tick.
        if (
          status.ui_phase === "completed" ||
          status.status === "completed" ||
          status.stage === "completed" ||
          status.progress >= 100
        ) {
          await finalizeAndGoToPreview();
          return;
        }

        if (status.status === "failed") {
          clearPoll();
          dispatch({ type: "GENERATION_ERROR", payload: status.message || "生成失败" });
        }
      } catch (fetchErr) {
        // RISK-T16-3 / F-3: Consecutive error handling (shot-gen, same logic as text-gen above).
        // Network errors show retry banner but do NOT trigger the fatal error page.
        shotGenErrorCount.current++;
        const isNetworkError =
          (typeof window !== "undefined" && !window.navigator.onLine) ||
          (fetchErr instanceof TypeError && /failed to fetch|network/i.test(fetchErr.message));
        if (isNetworkError) {
          setNetworkOffline(true);
          setShowRetryHint(true);
        } else if (shotGenErrorCount.current >= 3) {
          setShowRetryHint(true);
        }
        if (shotGenErrorCount.current >= 15 && !isNetworkError) {
          clearPoll();
          dispatch({ type: "GENERATION_ERROR", payload: "服务器连接异常，请稍后刷新页面重试" });
        }
      }
    };

    // RISK-T20-24 (Wave 4): Fire shot-gen poll immediately on mount so progress bar
    // shows real backend value (e.g. shots_completed/total) within ~200ms instead of
    // 2s delay. Fixes "progress doesn't reflect backend immediately on transition to shot-gen".
    void runShotGenPoll();
    pollRef.current = setInterval(runShotGenPoll, 2000);

    return () => clearPoll();
  }, [state.generationSubPhase, dispatch, useRealApi, token, projectId, clearPoll, finalizeAndGoToPreview]);

  // ============ Handlers ============
  // RISK-T20-25 (Wave 4): confirm-characters → /generating (Stage 3 LLM 跑中).
  // Previously (RISK-T14-6 design): push /scenes immediately + show ScenePreview "场景生成中"
  //   loading state. Problem: Wave 9 contract says ui_phase=scene_review_pending → /generating,
  //   so Watcher 5s tick saw scene_review_pending → dispatched SET_GENERATION_SUB_PHASE=text-gen
  //   → state→URL sync push /generating → race-loop /characters→/scenes→/generating→/scenes.
  //   Founder observed: "/characters → /scenes 加载 20s → /generating" (test19 5/19 21:25).
  // Fix (Wave 4): Don't push /scenes; let Watcher route to /scenes when backend ui_phase=scene_review
  //   (Stage 3 done). During Stage 3 running, user sees /generating progress bar = correct UX.
  //   subPhase set to "text-gen" (NOT scene-preview) — matches char_review_pending→scene_review_pending
  //   transition per Wave 9 ui_phase contract.
  const handleConfirmCharacters = useCallback(() => {
    dispatch({ type: "CONFIRM_CHARACTERS" });
    dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "text-gen" });
    // Push /generating (not /scenes) — Watcher will force /scenes when ui_phase=scene_review.
    const generatingUrl = buildCreateUrl(projectId, "generating");
    if (generatingUrl) {
      router.replace(generatingUrl);
    }
  }, [dispatch, projectId, router]);

  // T22-NEW-5 (2026-05-22): handleConfirmScenes removed — R4-2 scene_review checkpoint
  // deleted from frontend. Backend Wave 8 removes the pipeline wait loop and the
  // /projects/{id}/confirm-scenes endpoint call is no longer needed.

  // RISK-T14-12: "后台生成" — navigate to dashboard, let pipeline keep running.
  // On click: (1) request Notification permission so we can notify when done,
  // (2) push /dashboard (backend pipeline unaffected, continues in background).
  const handleBackgroundGenerate = useCallback(async () => {
    // Request browser Notification permission only when user explicitly asks for background gen
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission === "default") {
        try {
          await Notification.requestPermission();
        } catch {
          // Permission request failed or denied — proceed silently
        }
      }
    }
    router.push("/dashboard");
  }, [router]);

  // RISK-T17-8: "原地重启" — call POST /chapters/1/restart-from-failed-stage
  // then re-enter the generating phase so the pipeline continues from the failed stage.
  // Backend #2 is building this endpoint (Wave 12 parallel). If the endpoint is not yet
  // available, the call will fail and restartError will be set, surfacing the fallback
  // "返回重试" path to the user.
  const handleRestartFromFailedStage = useCallback(async () => {
    if (!projectId || !token) {
      setRestartError("无法重启：项目信息缺失，请尝试「返回重试」");
      return;
    }
    setRestartLoading(true);
    setRestartError(null);
    // eslint-disable-next-line no-console
    console.log("[StageC] RISK-T17-8: restart-from-failed-stage projectId=", projectId, "chapter=1");
    try {
      // Backend #2 (Wave 12) builds: POST /api/projects/{project_id}/chapters/1/restart-from-failed-stage
      await apiFetch<{ success: boolean; restarted_from_stage: number }>(
        `/projects/${projectId}/chapters/1/restart-from-failed-stage`,
        { method: "POST", body: JSON.stringify({}) },
        token
      );
      // eslint-disable-next-line no-console
      console.log("[StageC] RISK-T17-8: restart success — re-entering generating phase");
      // Reset error state and re-enter generating so pollers resume
      dispatch({ type: "START_GENERATION" });
      const generatingUrl = buildCreateUrl(projectId, "generating");
      if (generatingUrl) router.replace(generatingUrl);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "重启失败，请尝试「返回重试」";
      // eslint-disable-next-line no-console
      console.error("[StageC] RISK-T17-8: restart failed:", msg);
      setRestartError(msg);
    } finally {
      setRestartLoading(false);
    }
  }, [projectId, token, dispatch, router]);

  const isError = state.generationStatus === "error";

  // RISK-T19-2: Log full technical error message to console.error when entering failed state.
  // This keeps the technical stack trace in backend metrics/client.log even though
  // we no longer display it raw to users in the UI.
  useEffect(() => {
    if (isError && state.generationMessage) {
      // eslint-disable-next-line no-console
      console.error("[StageC] RISK-T19-2: Pipeline failed — full technical message:", state.generationMessage);
    }
  }, [isError, state.generationMessage]);

  // BUG-T13-REACT-ANTIPATTERN-STAGEC: stabilize prop callbacks with useCallback so
  // CharacterPreview / ScenePreview don't see "new function on every parent render".
  // Previously the inline arrow functions caused identity churn → re-renders cascaded
  // into countdown useEffects → stack trace pointed at CharacterPreview while
  // CreateProvider was being dispatched from a cascading effect.
  const handleUpdatePreviewCharacter = useCallback(
    (id: string, updates: Partial<PreviewCharacter>) => {
      dispatch({ type: "UPDATE_PREVIEW_CHARACTER", payload: { id, updates } });
    },
    [dispatch]
  );

  // T22-NEW-5 (2026-05-22): handleUpdatePreviewScene removed — R4-2 scene_review
  // checkpoint removed. UPDATE_PREVIEW_SCENE dispatch no longer needed.

  // ============ Render ============
  if (state.generationSubPhase === "char-preview") {
    return (
      <CharacterPreview
        characters={state.previewCharacters}
        onUpdateCharacter={handleUpdatePreviewCharacter}
        onConfirm={handleConfirmCharacters}
        projectId={projectId}
        token={token}
      />
    );
  }

  // T22-NEW-5 (2026-05-22): 砍 R4-2 — scene-preview render 块已整段移除.
  //   旧逻辑: subPhase=scene-preview → <ScenePreview> 文字层场景确认 (调 handleConfirmScenes)
  //   新逻辑: Pipeline 直接 Stage 3 → Stage 4, 用户只在 scene-refs-preview (R4-3) 视觉确认.
  //   ScenePreview 组件本身保留 (未删除 class), 只移除 render 入口分支.

  // T21-NEW-7 (2026-05-21 DEC-047 v1.4): scene-refs-preview 真场景视觉确认 (R4-3)
  // 镜像 CharacterPreview 对偶设计 — 卡片 (interior + exterior 2 图) + 编辑 + 重生 + 60s 倒计时.
  // 与 ScenePreview (R4-2 情节文字确认) 严格区分 — 这里看的是真生成的场景参考图.
  if (state.generationSubPhase === "scene-refs-preview") {
    return (
      <SceneRefsPreview
        projectId={projectId}
        token={token}
      />
    );
  }

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-lg mx-auto text-center"
      >
        <motion.div
          className="mb-8"
          animate={isError ? {} : { scale: [1, 1.05, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          {isError ? (
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto" />
          ) : (
            <Loader2 className="w-16 h-16 text-brand-primary mx-auto animate-spin" />
          )}
        </motion.div>

        <h1 className="text-2xl font-bold mb-2">
          {resolvePhaseTitle(isError, state.generationSubPhase, currentStage)}
        </h1>
        {/* UX-12 / P2-4: sub-title is stage-aware. Completed stage shows message only.
            RISK-T19-2: Error state subtitle is kept brief — full friendly UI (with restart button
            + collapsible tech details) is rendered in the isError block below.
            RISK-T19-3: Use resolveSubtitle(currentStage) for ALL generating states (not just
            shot-gen). This shows the stage-specific copy ("AI 正在创作故事，请稍候" for storyboard)
            instead of the generic "AI 正在全力创作，请耐心等待" which was shown during
            the storyboard stage because subPhase is "text-gen" (watcher mapping). */}
        <p className="text-text-tertiary text-sm mb-8">
          {isError
            ? "生成遇到问题"
            : (currentStage === "completed" || state.generationProgress >= 100)
              ? (state.generationMessage || "故事生成完成！")
              : resolveSubtitle(currentStage)}
        </p>

        {!isError && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-muted">进度</span>
              <span className="text-xs text-text-muted">{state.generationProgress}%</span>
            </div>
            <div className="w-full h-2 bg-bg-secondary rounded-full overflow-hidden">
              {/* P3-6: spring transition for smooth progress bar animation instead of jumpy 35→65→100 */}
              <motion.div
                className="h-full bg-gradient-to-r from-brand-primary to-purple-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${state.generationProgress}%` }}
                transition={{ type: "spring", stiffness: 60, damping: 20, mass: 1 }}
              />
            </div>
            {/* Wave 11.3 / RISK-T17-5: ETA display now driven by useETA hook.
                etaText is null for review stages / completed — hook handles all guard logic. */}
            {state.generationProgress < 100 && etaText !== null && (
              <p className="text-xs text-text-muted mt-2">
                {etaText}
              </p>
            )}
            {/* TASK-FRONTEND-STALE-COPY: Stage-aware progress tip — updates as pipeline stage advances.
                Shown during text-gen (all stages up to character_ready) and shot-gen (image/bgm stages).
                Copy transitions: story_generation/character_design → "confirm coming up (cocoa)"
                                  screenplay/storyboard → "scripting done, drawing soon"
                                  image_preparation/image_generation → "drawing frames now"
                                  bgm/music → "last step" */}
            {(state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen") &&
              getProgressTip(currentStage, state.generationSubPhase) && (
              <p className="text-xs text-text-tertiary mt-3 opacity-80">
                {getProgressTip(currentStage, state.generationSubPhase)}
              </p>
            )}
          </div>
        )}

        {!isError && state.generationMessage && (
          <motion.p
            key={state.generationMessage}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-brand-primary mb-6"
          >
            {/* UX-8: replace "张图像" with "个片段" for user-friendly copy */}
            {friendlyMessage(state.generationMessage)}
          </motion.p>
        )}

        {/* P2-2: checkpointPreview removed (was stale 55-63% threshold, replaced by character_ready stage event) */}

        {/* RISK-T16-3 / F-3: Network retry indicator.
            - networkOffline=true → explicit "网络连接中断" message (not "生成遇到问题")
            - showRetryHint=true (non-network, 3-14 errors) → generic retry hint
            Both are hidden once the next successful poll clears the state. */}
        {!isError && networkOffline && (
          <p className="text-amber-400 text-xs mb-4 flex items-center justify-center gap-1">
            网络连接中断，正在等待恢复...（后台生成继续进行，请保持页面打开）
          </p>
        )}
        {!isError && showRetryHint && !networkOffline && (
          <p className="text-text-muted text-xs mb-4">
            网络波动中，正在重试...
          </p>
        )}

        {/* RF-3: Carousel tips (19 tips, no cocoa) — shown during text-gen and shot-gen, above log */}
        {(state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen") && !isError && (
          <div className="mb-6 h-10 flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={tipIndex}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.4 }}
                className="text-text-tertiary text-xs"
              >
                {CAROUSEL_TIPS[tipIndex]}
              </motion.p>
            </AnimatePresence>
          </div>
        )}

        {/* RF-2: Filter technical errors from generation log */}
        {state.generationLog.filter(e => friendlyError(e.message) === e.message).length > 0 && (
          <div className="bg-bg-secondary rounded-xl p-4 border border-white/5 text-left max-h-48 overflow-y-auto">
            <div className="space-y-2">
              {state.generationLog
                .filter(e => friendlyError(e.message) === e.message)
                .map((entry, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0" />
                  {/* T-1: also apply friendlyMessage to log entries ("张图像" → "个片段") */}
                  <span className="text-text-tertiary">{friendlyMessage(entry.message)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Wave 13 #4B (P2-3 fix): "后台生成" button visibility — fix the "忽有忽无" flicker.
            The button used to show during storyboard (text-gen + currentStage="storyboard") AND
            during shot-gen. But storyboard happens BEFORE scene confirmation (R4-3), so the button
            appeared at storyboard → disappeared at scene_image_preparation → reappeared after scene
            confirm = flickering, confusing.

            ROOT CAUSE: the old RISK-T17-7 assumption "at storyboard the user already confirmed
            scenes" was wrong — scene confirmation (scenesConfirmed) only fires at R4-3 (after
            scene_references_ready), which is AFTER storyboard.

            FIX (single source of truth = scenesConfirmed): hide the button through the ENTIRE
            pre-scene-confirm flow (story_generation / character_design / screenplay / storyboard /
            scene_image_preparation) and show it consistently ONLY after scenes are confirmed
            (image_preparation / image_generation / bgm / music — all shot-gen subPhase). This
            mirrors STAGE_SUBTITLE which only says "可以选择后台生成" for those same post-confirm
            stages. scenesConfirmed is backend-authoritative (hydrated from scenes_confirmed) so it
            survives page re-entry mid-generation. */}
        {state.scenesConfirmed &&
          state.generationSubPhase === "shot-gen" &&
          !isError && (
          <button
            onClick={handleBackgroundGenerate}
            className="mt-6 py-2.5 px-6 rounded-lg border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors cursor-pointer"
          >
            后台生成，去做别的
          </button>
        )}

        {/* RISK-T19-2 / RISK-T17-8: Friendly failed UI with "原地重启" + "返回重试" + collapsible tech details */}
        {isError && (
          <div className="mt-6 space-y-3 text-left max-w-sm mx-auto">
            {/* Friendly description */}
            <p className="text-text-tertiary text-sm text-center">
              故事生成过程中遇到了一些技术问题，我们已记录并会尽快修复。你可以选择：
            </p>

            {/* Restart error feedback */}
            {restartError && (
              <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
                <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-300">{restartError}</p>
              </div>
            )}

            {/* Primary CTA: 原地重启 */}
            <button
              onClick={handleRestartFromFailedStage}
              disabled={restartLoading}
              className="w-full flex flex-col items-center justify-center gap-0.5 px-6 py-3 rounded-xl bg-brand-primary text-white font-medium hover:bg-brand-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span className="flex items-center gap-2">
                {restartLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                {restartLoading ? "重启中..." : "原地重启（从失败步骤继续）"}
              </span>
              {!restartLoading && (
                <span className="text-xs text-white/70">不浪费已有进度</span>
              )}
            </button>

            {/* Secondary CTA: 返回重试 */}
            <button
              onClick={() => dispatch({ type: "SET_STAGE", payload: "confirm" })}
              disabled={restartLoading}
              className="w-full flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              返回重试（重新创建故事）
            </button>

            {/* Collapsible tech details */}
            <button
              onClick={() => setShowTechDetails((v) => !v)}
              className="w-full flex items-center justify-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors py-1"
            >
              {showTechDetails ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
              {showTechDetails ? "收起技术详情" : "查看技术详情"}
            </button>
            {showTechDetails && (
              <div className="rounded-lg bg-bg-secondary border border-white/5 p-3">
                <p className="text-[11px] text-text-muted font-mono leading-relaxed break-all whitespace-pre-wrap select-all">
                  {state.generationMessage || "（无错误信息）"}
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </main>
  );
}

// ============ Character Preview Checkpoint ============

function CharacterPreview({
  characters,
  onUpdateCharacter,
  onConfirm,
  projectId,
  token,
}: {
  characters: PreviewCharacter[];
  onUpdateCharacter: (id: string, updates: Partial<PreviewCharacter>) => void;
  onConfirm: () => void;
  projectId: string | null;
  token: string | null;
}) {
  const { toast } = useToast();
  const router = useRouter();
  // D.14 F-Lock-Family: lock character preview once generation has started/completed
  const isLocked = useStageLock();
  const progressUrl = buildCreateUrl(projectId, "generating") || "/dashboard";
  // RISK-T20-12 + B58 align: 60s countdown (Founder 5/19 decision, align with /scenes)
  // Upgraded from 20s → 60s to match ScenePreview (B58). Anti-pattern fix: setInterval
  // only does pure state update; side-effect (handleConfirmWithApi) triggered by a
  // separate useEffect watching countdown===0 (RISK-T20-15 fix pattern).
  const [countdown, setCountdown] = useState(60);
  const [paused, setPaused] = useState(false);
  const [adjustingId, setAdjustingId] = useState<string | null>(null);
  const [adjustInput, setAdjustInput] = useState("");
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  // P2-1 (Wave 12 / STATUS_API_CONTRACT §9.7): friendly loading text for the in-flight
  // adjust job. Backend now returns 202 + job_id, then we poll adjust-jobs/{job_id}.
  // We show stage_message + progress so the user sees "AI 重绘中…" rather than a frozen spinner.
  const [adjustJobMsg, setAdjustJobMsg] = useState<string>("");
  // B26: track per-character portrait load failure (img onError → show error placeholder)
  const [portraitErrors, setPortraitErrors] = useState<Record<string, boolean>>({});

  // BUG-T13-REACT-ANTIPATTERN-STAGEC: moved B36 render-time console.log into useEffect.
  // Logging during render is technically safe but creates render-loop noise + may
  // confuse React DevTools strict-mode double-render detection.
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.log(
      "[B36][CharacterPreview] mount/update: characters.length=",
      characters.length,
      "projectId=",
      projectId,
      "isLocked=",
      isLocked
    );
  }, [characters.length, projectId, isLocked]);

  // B26: Component-level portrait URL fallback — when state.previewCharacters[].portraitUrl
  // is null (e.g. when /chapters/1/story returned 404 at character_ready stage),
  // construct the static URL directly from projectId + char.id.
  // This is a last-resort safety net so CharacterPreview never shows empty portrait areas.
  //
  // BUG-T13-REACT-ANTIPATTERN-STAGEC: removed console.log inside this useCallback because
  // it was called twice per character per render (once for the truthy check at L1130,
  // once for the src at L1135), inflating log volume by 2x and obscuring real signals.
  const resolvePortraitUrl = useCallback((char: PreviewCharacter): string | null => {
    if (char.portraitUrl) return toAbsoluteUrl(char.portraitUrl);
    // Fallback: construct static URL from projectId + char.id (char_001 format)
    if (projectId && char.id && /^char_\d+/.test(char.id)) {
      const staticPath = `/static/outputs/${projectId}/character_refs/${char.id}_portrait.png`;
      return toAbsoluteUrl(staticPath);
    }
    return null;
  }, [projectId]);

  // BUG-T13-REACT-ANTIPATTERN-STAGEC: pre-compute portraits once per render so the JSX
  // calls resolvePortraitUrl once per character (not twice — at the &&-check and the src).
  // This eliminates duplicate work and any side-effect cascade from the function.
  // Uses useMemo with a Map keyed by character id; recomputes only when characters or
  // resolvePortraitUrl identity changes (not on every render).
  const portraitMap = useMemo(() => {
    const m = new Map<string, string | null>();
    characters.forEach((c) => m.set(c.id, resolvePortraitUrl(c)));
    return m;
  }, [characters, resolvePortraitUrl]);
  const confirmedRef = useRef(false); // R4-1: prevent double-confirm
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  // R4-1 / R6-3: Immediately transition to scene-preview, then fire API in background
  const handleConfirmWithApi = useCallback(async () => {
    if (confirmedRef.current) return; // prevent double call
    confirmedRef.current = true;
    clearTimer();
    // [B36] Log — confirm fired (auto or manual)
    // eslint-disable-next-line no-console
    console.log("[B36][CharacterPreview] handleConfirmWithApi: confirming characters. characters.length=", characters.length, "projectId=", projectId);
    // R6-3: Clear any in-progress adjust UI immediately to avoid stale panels
    setAdjustingId(null);
    setRegeneratingId(null);
    // R6-3: Transition to scene-preview immediately — do not wait for API
    onConfirm();
    // Fire confirm-characters API in background (pipeline unblocks server-side)
    if (projectId && token) {
      try {
        await apiFetch<{ success: boolean }>(
          `/projects/${projectId}/confirm-characters`,
          { method: "POST", body: JSON.stringify({}) },
          token
        );
      } catch {
        // API failure is non-fatal — pipeline has a 30-min timeout fallback
      }
    }
  }, [projectId, token, onConfirm, clearTimer, characters.length]);

  const hasCharacters = characters.length > 0;

  // B50-mirror: when characters first arrive, reset countdown to 60 so user always gets full window
  useEffect(() => {
    if (hasCharacters) {
      setCountdown(60); // RISK-T20-12 + B58: 60s (upgraded from 20s to align with /scenes)
    }
  }, [hasCharacters]);

  // RISK-T20-12 + B58 align: 60s auto-confirm timer using T20-15 anti-pattern fix.
  // setInterval ONLY does pure state update (setCountdown). No side-effects inside updater.
  // B36 gate: !hasCharacters → clearTimer (mirrors B42/B50 pattern in ScenePreview).
  // D.14: isLocked → clearTimer (characters already confirmed, generation started).
  // Adjust paused → clearTimer so user has time to review adjustments.
  useEffect(() => {
    if (!hasCharacters) { clearTimer(); return; } // B36 gate: wait for character data
    if (isLocked) { clearTimer(); return; }       // D.14: already past char-preview stage
    if (paused) { clearTimer(); return; }
    // RISK-T20-15 anti-pattern fix: only pure state update inside setInterval callback.
    // Side-effect (handleConfirmWithApi) is triggered by a separate useEffect below.
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearTimer();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearTimer();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasCharacters, isLocked, paused, clearTimer]);

  // RISK-T20-15 anti-pattern fix: side-effect lives in its own useEffect, NOT inside
  // the setCountdown updater. This is the same pattern used in ScenePreview (L1662-1667).
  // React-safe: dispatch/API/routing only happen in useEffect, never in updater functions.
  useEffect(() => {
    if (countdown === 0 && !confirmedRef.current) {
      handleConfirmWithApi();
    }
  }, [countdown, handleConfirmWithApi]);

  const handleAdjust = (charId: string) => {
    setPaused(true); // RISK-T20-12: pause countdown while user is adjusting a character
    setAdjustingId(charId);
    setAdjustInput("");
  };

  // Wave 12 + Wave 13 #6: shared async job shape for character adjust + regenerate-portrait.
  // STATUS_API_CONTRACT §9.7.2 (poll endpoint) + §9.7.4 (regenerate-portrait async):
  // both kinds use the SAME GET /characters/adjust-jobs/{job_id} poller, distinguished by `kind`.
  interface CharacterJob {
    job_id: string;
    char_id: string;
    kind?: "adjust" | "regenerate_portrait";
    status: "pending" | "processing" | "completed" | "failed";
    progress?: number | null;
    stage_message?: string | null;
    result?: {
      success?: boolean;
      character?: { description?: string; description_zh?: string };
      char_id?: string;
      portrait_url?: string | null;
      fullbody_url?: string | null;
      message?: string;
    } | null;
    error?: string | null;
  }

  // Wave 12 + Wave 13 #6: shared poller for the async character job endpoint.
  // Polls GET /characters/adjust-jobs/{job_id} until status ∈ {completed, failed}.
  // Used by BOTH handleApplyAdjustment (adjust, kind="adjust") and handleRegenerate
  // (reroll, kind="regenerate_portrait") — same endpoint, derive UI purely from
  // backend status + progress + stage_message (DEC-030 backend authoritative, no local guess).
  //
  // onComplete receives the job.result so callers can apply kind-specific updates
  // (adjust records the adjustment text; reroll just swaps the portrait).
  const pollCharacterJob = async (
    jobId: string,
    charId: string,
    onComplete: (result: NonNullable<CharacterJob["result"]>) => void
  ): Promise<void> => {
    const POLL_INTERVAL_MS = 2000;
    const MAX_POLLS = 120; // safety cap: 120 × 2s = 4 min (well past the ~60-90s backend job)
    let polls = 0;
    // small initial delay so the job has a chance to register before first poll
    await new Promise((r) => setTimeout(r, 800));
    while (polls < MAX_POLLS) {
      polls += 1;
      let job: CharacterJob;
      try {
        job = await apiFetch<CharacterJob>(
          `/projects/${projectId}/characters/adjust-jobs/${jobId}`,
          {},
          token,
          { silentStatuses: [404] } // 404 = expired/not-yet-registered; retry a few times
        );
      } catch {
        // Transient (e.g. job not yet registered, or brief network blip) — keep polling.
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        continue;
      }

      // Derive friendly loading text from backend stage_message + progress (§9.7.2/§9.7.4).
      const pct = typeof job.progress === "number" ? Math.max(0, Math.min(100, job.progress)) : null;
      const stageMsg = job.stage_message || "AI 重绘中";
      setAdjustJobMsg(pct !== null ? `${stageMsg} ${pct}%` : `${stageMsg}…`);

      if (job.status === "completed") {
        onComplete(job.result || {});
        return;
      }

      if (job.status === "failed") {
        // eslint-disable-next-line no-console
        console.warn("[StageC] character job failed:", job.error || "(no error message)");
        toast("error", job.error ? `操作失败：${job.error}` : "操作失败，请重试");
        return;
      }

      // pending / processing → wait then poll again
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    }
    toast("error", "操作超时，请稍后重试");
  };

  // Cache-buster so the browser reloads the overwritten portrait/fullbody at the same path.
  const bustUrl = (u: string | null | undefined): string | null => {
    const abs = toAbsoluteUrl(u);
    if (!abs) return null;
    return abs.includes("?") ? `${abs}&_=${Date.now()}` : `${abs}?_=${Date.now()}`;
  };

  // F-2 + Wave 13 #6: regenerate-portrait (reroll) — now ASYNC + polling.
  // STATUS_API_CONTRACT §9.7.4 (Backend Wave 13 #6 changed this endpoint to async):
  //   1. POST /characters/{char_id}/regenerate-portrait → 202 Accepted + { job_id, status }
  //      (no longer 200 + { portrait_url } — old synchronous behavior would break here)
  //   2. poll GET /characters/adjust-jobs/{job_id} (kind="regenerate_portrait") until terminal
  //   3. completed → read result.portrait_url (cache-buster) to refresh the character card
  // Reuses pollCharacterJob — identical poller as adjust, only the POST endpoint + completion
  // handling differ (reroll just swaps the portrait, records no adjustment text).
  const handleRegenerate = async (charId: string) => {
    if (!projectId || !token) {
      toast("error", "重新生成失败，请稍后重试");
      return;
    }
    setRegeneratingId(charId);
    setAdjustJobMsg("AI 重绘中，请稍候…");

    // 1) Kick off the async job — backend returns 202 + job_id (does NOT block ~60s).
    let jobId: string;
    try {
      const kickoff = await apiFetch<{ success: boolean; job_id: string; status: string; char_id: string; message?: string }>(
        `/projects/${projectId}/characters/${charId}/regenerate-portrait`,
        { method: "POST", body: JSON.stringify({}) },
        token
      );
      if (!kickoff.job_id) throw new Error("missing job_id in regenerate-portrait 202 response");
      jobId = kickoff.job_id;
    } catch {
      // Fast-validation failure (404/400) — surface immediately, no polling.
      setRegeneratingId(null);
      setAdjustJobMsg("");
      toast("error", "重新生成失败，请稍后重试");
      return;
    }

    // 2) Poll until terminal. Reroll just swaps the portrait on completion.
    try {
      await pollCharacterJob(jobId, charId, (result) => {
        const newPortrait = bustUrl(result.portrait_url);
        if (newPortrait) {
          onUpdateCharacter(charId, { portraitUrl: newPortrait });
        }
        // Clear any stale img-error flag so the refreshed portrait shows.
        setPortraitErrors((prev) => ({ ...prev, [charId]: false }));
        toast("success", "已重新生成");
      });
    } finally {
      setRegeneratingId(null);
      setAdjustJobMsg("");
    }
  };

  // RF-5 / P2-1 (Wave 12): Real API for character adjustment — now ASYNC + polling.
  //
  // STATUS_API_CONTRACT §9.7 (test26 实证: 旧同步阻塞 90s → 前端死等转圈 + 超时重发 3 次):
  //   1. POST /characters/{char_id}/adjust → 202 Accepted + { job_id, status: "pending" }
  //      (不再同步等 90s 才返回)
  //   2. 轮询 GET /characters/adjust-jobs/{job_id} 每 2s, 直到 status ∈ {completed, failed}
  //   3. completed → 读 result.portrait_url / fullbody_url 刷新角色卡 (cache-buster)
  //   4. failed → 读 error 提示用户
  //   轮询期间显示 progress + stage_message (友好提示, 不再死等转圈)
  //
  // DEC-030 backend authoritative: 前端只按 status + progress 派生 loading UI,
  // 不本地猜测 90s 完成时间.
  const handleApplyAdjustment = async (charId: string) => {
    // B48: leave-empty = reroll (no prompt change, just new seed).
    // Wave 13 #6: reroll now goes through the ASYNC regenerate-portrait endpoint
    // (§9.7.4) — handleRegenerate kicks off the 202 job + polls, same as adjust.
    if (!adjustInput.trim()) {
      setAdjustingId(null);
      await handleRegenerate(charId);
      return;
    }

    if (!projectId || !token) {
      toast("error", "调整失败，请重试");
      return;
    }

    const adjustment = adjustInput.trim();
    setRegeneratingId(charId);
    setAdjustJobMsg("AI 重绘中，请稍候…");

    // 1) Kick off the async job — backend returns 202 + job_id (does NOT block ~90s).
    let jobId: string;
    try {
      const kickoff = await apiFetch<{ success: boolean; job_id: string; status: string; char_id: string; message?: string }>(
        `/projects/${projectId}/characters/${charId}/adjust`,
        { method: "POST", body: JSON.stringify({ adjustment }) },
        token
      );
      if (!kickoff.job_id) throw new Error("missing job_id in adjust 202 response");
      jobId = kickoff.job_id;
    } catch {
      // Fast-validation failure (404/400/500) — surface immediately, no polling.
      setRegeneratingId(null);
      setAdjustingId(null);
      setAdjustJobMsg("");
      toast("error", "调整失败，请重试");
      return;
    }

    // 2) Poll until terminal via the shared poller (§9.7.2). We DON'T guess a 90s timer —
    //    the loading UI is purely derived from backend status + progress + stage_message.
    //    On completion, adjust ALSO records the adjustment text + updated description.
    try {
      await pollCharacterJob(jobId, charId, (result) => {
        const char = characters.find((c) => c.id === charId);
        const newPortrait = bustUrl(result.portrait_url);
        if (char) {
          onUpdateCharacter(charId, {
            description: result.character?.description_zh || result.character?.description || char.description,
            ...(newPortrait ? { portraitUrl: newPortrait } : {}),
            adjustments: [...char.adjustments, adjustment],
          });
        }
        // Clear any stale img-error flag so the refreshed portrait shows.
        setPortraitErrors((prev) => ({ ...prev, [charId]: false }));
        toast("success", "角色已更新");
      });
    } finally {
      setRegeneratingId(null);
      setAdjustingId(null);
      setAdjustJobMsg("");
    }
  };

  return (
    <main className="container-lg py-8 pb-24">
      {/* D.14 F-Lock-Family: lock banner when generation already started beyond char-preview */}
      {isLocked && (
        <div className="mb-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3">
            <p className="text-amber-400 text-sm">
              📌 角色已确认，AI 正在创作画面。如需修改请新建项目
            </p>
            <button
              onClick={() => router.replace(progressUrl)}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors whitespace-nowrap"
            >
              返回创作进度
            </button>
          </div>
        </div>
      )}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <User className="w-5 h-5 text-brand-primary" />
              <h1 className="text-xl font-bold">角色预览</h1>
            </div>
            <p className="text-text-tertiary text-sm">确认角色外观，或调整后继续</p>
          </div>
          {/* RISK-T20-12 + B58 align: 60s countdown badge (Founder 5/19 decision, align with /scenes).
              D.14: Hide when locked; B36: hide when no characters yet; paused: hide when adjusting. */}
          {!paused && !isLocked && hasCharacters && (
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">
                {countdown}
              </div>
              <span className="text-xs text-text-muted hidden sm:inline">秒后自动继续</span>
            </div>
          )}
        </div>

        {/* B36: Placeholder UI when characters have not loaded yet — prevents empty grid + blocks confirm */}
        {!hasCharacters && (
          <div className="flex flex-col items-center justify-center gap-4 py-16 mb-6 rounded-xl border border-white/5 bg-bg-secondary/40">
            <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
            <div className="text-center">
              <p className="text-text-primary text-sm font-medium mb-1">角色还在生成中，请稍候…</p>
              <p className="text-text-muted text-xs">AI 正在设计角色外观，完成后将自动显示</p>
            </div>
          </div>
        )}

        <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6${!hasCharacters ? " hidden" : ""}`}>
          {characters.map((char) => {
            // BUG-T13-REACT-ANTIPATTERN-STAGEC: use pre-computed portrait once per char
            // (was being computed twice: in the && condition AND in src — now memoized in portraitMap).
            const charPortraitUrl = portraitMap.get(char.id) ?? null;
            return (
            <motion.div key={char.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden">
              {/* UX-1: Show real portrait if available, otherwise clear silhouette placeholder.
                  B26: Enhanced visibility — silhouette uses stronger colors so user can tell
                  there IS content even when portrait hasn't loaded yet.
                  img onError → mark portraitErrors[charId] = true → show error placeholder. */}
              <div className="relative aspect-[3/4] bg-bg-tertiary">
                {regeneratingId === char.id ? (
                  // P2-1 (Wave 12 §9.7): friendly loading with backend stage_message + progress
                  // instead of a bare spinner that looks frozen during the ~90s async job.
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-3 text-center">
                    <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                    <span className="text-text-secondary text-xs leading-snug">{adjustJobMsg || "AI 重绘中，请稍候…"}</span>
                  </div>
                ) : charPortraitUrl && !portraitErrors[char.id] ? (
                  // P0-3: Use plain <img> with toAbsoluteUrl to avoid Next.js Image domain restrictions.
                  // B26: resolvePortraitUrl() also applies the static-URL fallback when portraitUrl is null.
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={charPortraitUrl}
                    alt={char.name}
                    className="absolute inset-0 w-full h-full object-cover"
                    onError={() => {
                      // B26: portrait load failed — log and mark for fallback display
                      console.warn("[B26] portrait img load error for", char.id, "url:", char.portraitUrl, "resolved:", charPortraitUrl);
                      setPortraitErrors(prev => ({ ...prev, [char.id]: true }));
                    }}
                  />
                ) : (
                  // Silhouette / error placeholder — visible even in dark theme
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-bg-secondary/60">
                    {portraitErrors[char.id] ? (
                      <ImageOff className="w-12 h-12 text-text-muted/50" />
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="w-14 h-14 text-text-muted/50">
                        <circle cx="12" cy="7" r="4" />
                        <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" />
                      </svg>
                    )}
                    <span className="text-text-muted/70 text-xs font-medium">{portraitErrors[char.id] ? "图片加载失败" : char.name}</span>
                  </div>
                )}
                {/* B48: removed confusing RotateCcw top-right button.
                    Reroll (no-prompt regenerate) is now unified with the "调整 / 重生" button below:
                    leaving the input blank = reroll (same seed change, no prompt edit).
                    This avoids UX ambiguity between ⟲ and ✏️ and fixes mobile discoverability. */}
              </div>
              <div className="p-3">
                <p className="font-semibold text-text-primary text-sm mb-0.5">{char.name}</p>
                <p className="text-text-muted text-xs mb-2 line-clamp-2">{char.description}</p>
                {/* D.14: hide adjust button when locked */}
                {!isLocked && (
                  <button onClick={() => handleAdjust(char.id)} className="flex items-center gap-1 text-xs text-brand-primary hover:underline cursor-pointer"><Pencil className="w-3 h-3" />调整 / 重生</button>
                )}
              </div>
              <AnimatePresence>
                {adjustingId === char.id && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="border-t border-white/5 overflow-hidden">
                    <div className="p-3 space-y-2">
                      <div className="flex flex-wrap gap-1.5">
                        {ADJUST_TAGS.map((tag) => (
                          <button key={tag} onClick={() => setAdjustInput(tag)} className="px-2.5 py-1 rounded-full bg-bg-tertiary text-text-secondary text-xs hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer">{tag}</button>
                        ))}
                      </div>
                      {/* B48: placeholder explains leave-empty = reroll behavior */}
                      <input type="text" value={adjustInput} onChange={(e) => setAdjustInput(e.target.value)} placeholder="留空可换一张，填写描述可调整外观" className="w-full px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-xs placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50" />
                      <div className="flex gap-2">
                        <button onClick={() => handleApplyAdjustment(char.id)} className="flex-1 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary text-xs font-medium cursor-pointer">重新生成</button>
                        <button onClick={() => setAdjustingId(null)} className="flex-1 py-1.5 rounded-lg border border-white/10 text-text-secondary text-xs cursor-pointer">取消</button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
            );
          })}
        </div>

        {/* D.14: hide confirm button when locked; B36: hide when no characters loaded yet */}
        {!isLocked && hasCharacters && (
          <button onClick={handleConfirmWithApi} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
            确认角色，继续<ChevronRight className="w-4 h-4" />
          </button>
        )}
      </motion.div>
    </main>
  );
}

// ============ Scene Preview Checkpoint ============
// T22-NEW-5 (2026-05-22): ScenePreview component kept (not deleted) per task spec —
// "只移除 render 入口分支". R4-2 render block removed above. Backend Wave 8 will
// remove the pipeline wait loop; until then this component is preserved but unused.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function ScenePreview({
  scenes,
  onUpdateScene,
  onConfirm,
  projectId,
}: {
  scenes: PreviewScene[];
  onUpdateScene: (id: string, userEdit: string) => void;
  onConfirm: (modifiedScenes?: PreviewScene[]) => void;
  projectId: string | null;
}) {
  const router = useRouter();
  // D.14 F-Lock-Family: lock scene preview once generation has started/completed
  const isLocked = useStageLock();
  const progressUrl = buildCreateUrl(projectId, "generating") || "/dashboard";

  const [countdown, setCountdown] = useState(60); // B58: 60s countdown (was 20, Founder decision)
  const [paused, setPaused] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // B42+B50: scenes gate — only start countdown when scenes are actually loaded.
  // Without this, an empty scenes array triggers a 20s countdown → auto-confirm → user skips scene review
  // entirely without seeing any scenes. This mirrors the B36 hasCharacters gate pattern.
  // B50: extra guard — reset countdown when scenes first arrive so user always gets the full 20s.
  const hasScenes = scenes.length > 0;

  const clearTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  // B50: when scenes become available, reset countdown to 60 so user always gets the full window
  useEffect(() => {
    if (hasScenes) {
      setCountdown(60); // B58: 60s (was 20, Founder decision)
    }
  }, [hasScenes]);

  useEffect(() => {
    // B50 (stronger gate vs B42): countdown MUST NOT run when scenes are not yet loaded.
    // Order matters: !hasScenes check comes BEFORE paused check so the timer is always
    // killed immediately if backend hasn't returned scenes_json yet.
    if (!hasScenes) { clearTimer(); return; }  // B50: wait for backend scenes data
    if (paused) { clearTimer(); return; }
    // RISK-T20-15 (2026-05-19): pulled onConfirm OUT of the setCountdown updater.
    // React calls state updater functions during reconciliation, so side-effects
    // (especially context dispatches inside onConfirm → handleConfirmScenes →
    // dispatch) triggered React's "Cannot update CreateProvider while rendering
    // ScenePreview" warning. New pattern: setCountdown returns the next number
    // synchronously, and onConfirm is called from a guard outside the updater.
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearTimer();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearTimer();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasScenes, paused, clearTimer]);

  // RISK-T20-15 (2026-05-19): trigger auto-confirm in a separate effect when
  // countdown actually hits 0. Side-effect (dispatch via onConfirm) lives in
  // useEffect, not inside a state updater — React-safe.
  const confirmedRefScene = useRef(false);
  useEffect(() => {
    if (countdown === 0 && hasScenes && !paused && !confirmedRefScene.current) {
      confirmedRefScene.current = true;
      onConfirm(scenes);
    }
  }, [countdown, hasScenes, paused, onConfirm, scenes]);

  const handleEdit = (sceneId: string) => {
    setPaused(true);
    setEditingId(sceneId);
  };

  return (
    <main className="container-lg py-8 pb-24">
      {/* D.14 F-Lock-Family: lock banner when generation already started beyond scene-preview */}
      {isLocked && (
        <div className="mb-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3">
            <p className="text-amber-400 text-sm">
              📌 场景已确认，AI 正在创作画面。如需修改请新建项目
            </p>
            <button
              onClick={() => router.replace(progressUrl)}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors whitespace-nowrap"
            >
              返回创作进度
            </button>
          </div>
        </div>
      )}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-5 h-5 text-brand-primary" />
              <h1 className="text-xl font-bold">场景确认</h1>
            </div>
            <p className="text-text-tertiary text-sm">确认场景描述，或修改后开始绘制</p>
          </div>
          {/* D.14: Hide countdown when locked; B42: hide when hasScenes=false */}
          {/* B58: 60s countdown so user has enough time to read/edit all scenes */}
          {!paused && !isLocked && hasScenes && (
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">{countdown}</div>
              <span className="text-xs text-text-muted">秒后自动继续</span>
            </div>
          )}
        </div>

        {/* B42: placeholder UI when scenes not yet loaded (mirrors B36 hasCharacters pattern) */}
        {!hasScenes && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
            <p className="text-text-tertiary text-sm">场景还在生成中，请稍候...</p>
          </div>
        )}

        {hasScenes && (
          <div className="space-y-3 mb-6">
            {scenes.map((scene, idx) => (
              <motion.div key={scene.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="bg-bg-secondary rounded-xl border border-white/5 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-brand-primary font-medium">场景 {idx + 1}</span>
                      <span className="text-sm font-semibold text-text-primary">{scene.name}</span>
                    </div>
                    {/* D.14: no textarea when locked */}
                    {editingId === scene.id && !isLocked ? (
                      <textarea value={scene.userEdit || scene.description} onChange={(e) => onUpdateScene(scene.id, e.target.value)} placeholder="描述你想要的场景氛围" rows={3} className="w-full mt-2 px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50 resize-none" />
                    ) : (
                      <p className="text-text-tertiary text-sm leading-relaxed">{scene.userEdit || scene.description}</p>
                    )}
                  </div>
                  {/* D.14: hide edit/done button when locked */}
                  {!isLocked && (
                    editingId === scene.id ? (
                      <button onClick={() => setEditingId(null)} className="text-xs text-brand-primary hover:underline mt-1 flex-shrink-0 cursor-pointer">完成</button>
                    ) : (
                      <button onClick={() => handleEdit(scene.id)} className="flex items-center gap-1 text-xs text-text-muted hover:text-brand-primary transition-colors mt-1 flex-shrink-0 cursor-pointer"><Pencil className="w-3 h-3" />修改</button>
                    )
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* D.14: hide confirm button when locked; B42: hide when hasScenes=false */}
        {!isLocked && hasScenes && (
          <button onClick={() => onConfirm(scenes)} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
            <Play className="w-4 h-4" />确认场景，继续
          </button>
        )}
      </motion.div>
    </main>
  );
}

// ============ T21-NEW-7 v1.4 (2026-05-21 DEC-047): Scene References Preview Checkpoint ============
//
// 真场景视觉确认页面 (R4-3), 镜像 CharacterPreview 对偶设计:
//   - hydrate 真场景参考图 (GET /chapters/{n}/scene-references)
//   - 卡片显示 interior + exterior 2 张图 (每个 location 一张卡)
//   - 编辑场景描述 textarea + 重生 3 按钮 (interior / exterior / both)
//   - 60s 倒计时 (paused 时停, 编辑/重生时 paused)
//   - "确认场景, 继续生成画面" 按钮 (调 POST /confirm-scene-references)
//
// 与 ScenePreview (R4-2 情节文字确认) 严格区分:
//   - ScenePreview: 文字层面 (情节走向), hydrate /story.scenes (Stage 3 数据)
//   - SceneRefsPreview: 视觉层面 (真生成的 interior/exterior 参考图), hydrate /scene-references (Stage 4.5 数据)
//
// DEC-014 / DEC-009 保留 (backend 真做):
//   - 重生 interior + exterior 时, exterior 用刚生成的 interior 作参考
//   - 只重生 exterior 时, 用 disk 现有 interior 作参考
//   - frontend 只触发 + 显示 cache-buster URL
//
// API 契约 (STATUS_API_CONTRACT v1.4 §4.4 - §4.6):
//   GET /api/projects/{uuid}/chapters/{n}/scene-references
//     → { scene_references: SceneReference[], scene_references_ready, scene_references_confirmed, countdown_seconds }
//   POST /api/projects/{uuid}/chapters/{n}/scenes/{location_id}/regenerate-reference
//     Body: { ref_type: "interior" | "exterior" | "both", user_edit?: string }
//     → { success, location_id, interior_url, exterior_url, message }
//   POST /api/projects/{uuid}/chapters/{n}/confirm-scene-references
//     Body: 空
//     → { success, scene_references_confirmed, next_stage }

interface SceneReferenceItem {
  location_id: string;
  location_zh: string;
  interior_url: string | null;
  exterior_url: string | null;
  interior_description: string;
  exterior_description: string;
  description_zh: string;
  atmosphere: string;
  time_of_day: string;
  lighting_condition: string;
  key_visual_elements: string[];
}

interface SceneReferencesResponse {
  scene_references: SceneReferenceItem[];
  scene_references_ready: boolean;
  scene_references_confirmed: boolean;
  countdown_seconds: number;
  chapter_number: number;
  project_id: string;
}

interface RegenerateRefResponse {
  success: boolean;
  location_id: string;
  interior_url: string | null;
  exterior_url: string | null;
  message: string;
}

function SceneRefsPreview({
  projectId,
  token,
}: {
  projectId: string | null;
  token: string | null;
}) {
  const { toast } = useToast();
  const router = useRouter();
  // D.14 F-Lock-Family: lock scene refs preview once generation has advanced past R4-3
  const isLocked = useStageLock();
  const progressUrl = buildCreateUrl(projectId, "generating") || "/dashboard";

  // ---- State ----
  // scene_references: list hydrated from backend GET /scene-references
  const [sceneRefs, setSceneRefs] = useState<SceneReferenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [hydrateError, setHydrateError] = useState<string | null>(null);

  // 60s countdown + pause (mirror CharacterPreview / ScenePreview)
  const [countdown, setCountdown] = useState(60);
  const [paused, setPaused] = useState(false);

  // Per-location editing + regenerating state
  const [editingLocation, setEditingLocation] = useState<string | null>(null);
  const [editInput, setEditInput] = useState("");
  // regeneratingLocation: { location_id, ref_type } — what's currently being regenerated
  const [regeneratingLocation, setRegeneratingLocation] = useState<{
    location_id: string;
    ref_type: "interior" | "exterior" | "both";
  } | null>(null);

  // Image load error tracking (per location + ref_type)
  const [imgErrors, setImgErrors] = useState<Record<string, boolean>>({});

  const confirmedRef = useRef(false); // R4-3: prevent double-confirm
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Poll ref: keep hydrating until backend says scene_references_ready (Stage 4.5 still running)
  const hydratePollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const clearHydratePoll = useCallback(() => {
    if (hydratePollRef.current) {
      clearInterval(hydratePollRef.current);
      hydratePollRef.current = null;
    }
  }, []);

  // ---- Hydrate ----
  // Initial fetch + poll until scene_references_ready=true (Stage 4.5 may still be running).
  // Once data arrives, stop poll and start 60s countdown.
  const hydrate = useCallback(async (): Promise<boolean> => {
    if (!projectId || !token) return false;
    try {
      const resp = await apiFetch<SceneReferencesResponse>(
        `/projects/${projectId}/chapters/1/scene-references`,
        {},
        token,
        { silentStatuses: [404] }
      );
      setHydrateError(null);
      if (resp.scene_references && Array.isArray(resp.scene_references) && resp.scene_references.length > 0) {
        setSceneRefs(resp.scene_references);
        setLoading(false);
        return true; // 有数据 → 停止 poll
      }
      // 没数据但 endpoint 200 → Stage 4.5 还没跑完, 继续 poll
      setLoading(true);
      return false;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      // eslint-disable-next-line no-console
      console.warn("[SceneRefsPreview] hydrate failed (will retry):", msg);
      // 不立即 setHydrateError — 让 poll 自动重试, 多次失败再显
      return false;
    }
  }, [projectId, token]);

  useEffect(() => {
    if (!projectId || !token) return;
    let cancelled = false;
    let consecutiveErrors = 0;

    const runHydrate = async () => {
      if (cancelled) return;
      const success = await hydrate();
      if (success) {
        clearHydratePoll();
        // 数据到达 → reset countdown to 60 (镜像 CharacterPreview B50)
        setCountdown(60);
        consecutiveErrors = 0;
      } else {
        consecutiveErrors++;
        // 5 次连续失败 (10s) 还没数据 + 没 200 response → 显友好提示
        if (consecutiveErrors >= 5) {
          setHydrateError("场景参考图加载中, 如长时间无响应请刷新页面");
        }
      }
    };

    // 立即 fire + 2s 间隔 poll (与 StageC text-gen / shot-gen poller 一致)
    void runHydrate();
    hydratePollRef.current = setInterval(runHydrate, 2000);

    return () => {
      cancelled = true;
      clearHydratePoll();
    };
  }, [projectId, token, hydrate, clearHydratePoll]);

  const hasData = sceneRefs.length > 0;

  // P1 #3 (scenes): Prefetch all scene reference images when sceneRefs loads.
  // Scene refs show all scenes in a vertical list (no pagination), so preload all at once.
  // This prevents the 10-20s lag caused by 2.85MB+ PNGs over cross-ocean bandwidth.
  //
  // Plan A++ NOTE: SceneReferenceItem does NOT have thumbnail URL fields
  // (interior_url_thumb / exterior_url_thumb) — the backend scene-references endpoint
  // returns only interior_url + exterior_url. Progressive enhancement (thumb → full swap)
  // is therefore not applicable here. The prefetch below serves as the perf optimization:
  // images are loaded into browser cache before the user scrolls to them.
  useEffect(() => {
    if (!hasData) return;
    sceneRefs.forEach((ref) => {
      if (ref.interior_url) {
        const img = new Image();
        img.src = toAbsoluteUrl(ref.interior_url) ?? ref.interior_url;
      }
      if (ref.exterior_url) {
        const img = new Image();
        img.src = toAbsoluteUrl(ref.exterior_url) ?? ref.exterior_url;
      }
    });
  }, [sceneRefs, hasData]);

  // ---- Confirm handler (R4-3 闸门解锁) ----
  const handleConfirmWithApi = useCallback(async () => {
    if (confirmedRef.current) return; // prevent double call
    confirmedRef.current = true;
    clearTimer();
    clearHydratePoll();
    // eslint-disable-next-line no-console
    console.log("[SceneRefsPreview] T21-NEW-7 R4-3: confirming scene references. count=", sceneRefs.length, "projectId=", projectId);
    // 即时切换 sub-phase 让 Watcher / StageC 进入 shot-gen
    // (类似 handleConfirmCharacters: 不等 API await, 直接 transition)
    if (projectId) {
      const generatingUrl = buildCreateUrl(projectId, "generating");
      if (generatingUrl) {
        router.replace(generatingUrl);
      }
    }
    // Fire confirm-scene-references API in background — pipeline R4-3 wait loop unblocks server-side
    if (projectId && token) {
      try {
        await apiFetch<{ success: boolean; next_stage: string }>(
          `/projects/${projectId}/chapters/1/confirm-scene-references`,
          { method: "POST", body: JSON.stringify({}) },
          token
        );
        // eslint-disable-next-line no-console
        console.log("[SceneRefsPreview] T21-NEW-7 R4-3: confirm-scene-references API success, pipeline unlocked");
      } catch (err) {
        // Non-fatal: pipeline has 1800s timeout fallback so UI not blocked
        // eslint-disable-next-line no-console
        console.warn("[SceneRefsPreview] T21-NEW-7 R4-3: confirm API failed (non-fatal, pipeline auto-continue after timeout):", err);
      }
    }
  }, [projectId, token, sceneRefs.length, clearTimer, clearHydratePoll, router]);

  // ---- 60s countdown effect (镜像 CharacterPreview anti-pattern 修复) ----
  // setInterval 只做 pure state update (setCountdown). Side-effect 在独立 useEffect 触发.
  useEffect(() => {
    if (!hasData) { clearTimer(); return; }
    if (isLocked) { clearTimer(); return; }
    if (paused) { clearTimer(); return; }
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearTimer();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearTimer();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasData, isLocked, paused, clearTimer]);

  // Side-effect: countdown==0 触发 auto-confirm (React-safe, useEffect 中)
  useEffect(() => {
    if (countdown === 0 && hasData && !paused && !confirmedRef.current) {
      handleConfirmWithApi();
    }
  }, [countdown, hasData, paused, handleConfirmWithApi]);

  // ---- Edit / Regenerate handlers ----
  const handleEdit = (locationId: string, currentDesc: string) => {
    setPaused(true); // 编辑时停倒计时
    setEditingLocation(locationId);
    setEditInput(currentDesc);
  };

  const handleRegenerate = async (
    locationId: string,
    refType: "interior" | "exterior" | "both",
    userEdit?: string
  ) => {
    if (!projectId || !token) return;
    setPaused(true); // 重生时停倒计时
    setRegeneratingLocation({ location_id: locationId, ref_type: refType });
    try {
      const body: { ref_type: string; user_edit?: string } = { ref_type: refType };
      if (userEdit && userEdit.trim()) {
        body.user_edit = userEdit.trim();
      }
      const result = await apiFetch<RegenerateRefResponse>(
        `/projects/${projectId}/chapters/1/scenes/${locationId}/regenerate-reference`,
        { method: "POST", body: JSON.stringify(body) },
        token
      );
      // 更新本地 sceneRefs — 用 cache-buster URL 替换 (backend 真返回 ?v={epoch})
      setSceneRefs((prev) =>
        prev.map((ref) => {
          if (ref.location_id !== locationId) return ref;
          const updated = { ...ref };
          if (result.interior_url) {
            updated.interior_url = result.interior_url;
            if (userEdit && (refType === "interior" || refType === "both")) {
              updated.interior_description = userEdit.trim();
            }
          }
          if (result.exterior_url) {
            updated.exterior_url = result.exterior_url;
            if (userEdit && (refType === "exterior" || refType === "both")) {
              updated.exterior_description = userEdit.trim();
            }
          }
          return updated;
        })
      );
      // 清编辑状态
      setEditingLocation(null);
      setEditInput("");
      // 清错误 (新 URL → 清旧错误标记)
      setImgErrors((prev) => {
        const next = { ...prev };
        delete next[`${locationId}_interior`];
        delete next[`${locationId}_exterior`];
        return next;
      });
      toast("success", `场景已重新生成 (${refType === "both" ? "内+外景" : refType === "interior" ? "内景" : "外景"})`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "重生失败";
      // eslint-disable-next-line no-console
      console.error("[SceneRefsPreview] regenerate failed:", msg);
      toast("error", `重新生成失败: ${msg}`);
    } finally {
      setRegeneratingLocation(null);
      // 注意: 不自动 resume countdown (paused=true 保留) — 用户可能想检查更多 location
      // 用户点 "继续" 或刷新页面时重置 paused
    }
  };

  const resumeCountdown = () => {
    setPaused(false);
    setCountdown(60); // 重新计时 60s (给用户全窗口)
  };

  // ---- Helper: 判断某 location_id + ref_type 是否正在重生 ----
  const isRegenerating = (locationId: string, refType: "interior" | "exterior"): boolean => {
    if (!regeneratingLocation) return false;
    if (regeneratingLocation.location_id !== locationId) return false;
    return regeneratingLocation.ref_type === "both" || regeneratingLocation.ref_type === refType;
  };

  return (
    <main className="container-lg py-8 pb-24">
      {/* D.14 F-Lock-Family lock banner */}
      {isLocked && (
        <div className="mb-6 max-w-3xl mx-auto">
          <div className="flex items-center justify-between gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3">
            <p className="text-amber-400 text-sm">
              📌 场景视觉已确认，AI 正在创作画面。如需修改请新建项目
            </p>
            <button
              onClick={() => router.replace(progressUrl)}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors whitespace-nowrap"
            >
              返回创作进度
            </button>
          </div>
        </div>
      )}

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-5 h-5 text-brand-primary" />
              <h1 className="text-xl font-bold">场景视觉预览</h1>
            </div>
            <p className="text-text-tertiary text-sm">
              确认场景参考图风格，或编辑后重新生成
            </p>
          </div>
          {/* 60s 倒计时徽章 (镜像 CharacterPreview/ScenePreview, paused 时隐藏) */}
          {!paused && !isLocked && hasData && (
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">
                {countdown}
              </div>
              <span className="text-xs text-text-muted hidden sm:inline">秒后自动继续</span>
            </div>
          )}
          {/* paused 时显 resume 按钮 */}
          {paused && !isLocked && hasData && (
            <button
              onClick={resumeCountdown}
              className="text-xs px-3 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary hover:bg-brand-primary/25 transition-colors"
            >
              继续倒计时
            </button>
          )}
        </div>

        {/* Loading state (Stage 4.5 还没跑完 / hydrate 进行中) */}
        {loading && (
          <div className="flex flex-col items-center justify-center gap-4 py-16 mb-6 rounded-xl border border-white/5 bg-bg-secondary/40">
            <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
            <div className="text-center">
              <p className="text-text-primary text-sm font-medium mb-1">场景参考图生成中，请稍候…</p>
              <p className="text-text-muted text-xs">AI 正在为每个场景准备 内景 + 外景 参考图</p>
            </div>
            {hydrateError && (
              <p className="text-amber-400 text-xs mt-2">{hydrateError}</p>
            )}
          </div>
        )}

        {/* Scene reference cards */}
        {!loading && hasData && (
          <div className="space-y-4 mb-6">
            {sceneRefs.map((ref, idx) => {
              const interiorErrKey = `${ref.location_id}_interior`;
              const exteriorErrKey = `${ref.location_id}_exterior`;
              const interiorRegenerating = isRegenerating(ref.location_id, "interior");
              const exteriorRegenerating = isRegenerating(ref.location_id, "exterior");
              const isEditingThis = editingLocation === ref.location_id;

              // T22-NEW-2: Smart display mode — determine what images actually exist.
              // Backend by-design only generates what makes sense (DEC-014/DEC-009):
              //   洞穴/海底 → interior only, 海面/沙滩 → exterior only, 渔村 → both.
              // We must never show empty placeholder slots — that causes user anxiety.
              const hasInterior = !!ref.interior_url;
              const hasExterior = !!ref.exterior_url;
              const hasBoth = hasInterior && hasExterior;
              const hasNone = !hasInterior && !hasExterior;

              // Layout: grid-cols-2 only when both images exist; otherwise full-width single image.
              const gridClass = hasBoth ? "grid grid-cols-1 sm:grid-cols-2 gap-0" : "grid grid-cols-1 gap-0";

              // Informative label shown below image for single-image cases (helps user understand by-design, not missing).
              let sceneTypeLabel: string | null = null;
              if (hasInterior && !hasExterior) {
                sceneTypeLabel = "(室内场景，无室外画面)";
              } else if (hasExterior && !hasInterior) {
                sceneTypeLabel = "(室外场景，无室内画面)";
              }

              return (
                <motion.div
                  key={ref.location_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden"
                >
                  {/* Card header: location name + meta */}
                  <div className="p-4 border-b border-white/5">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs text-brand-primary font-medium">场景 {idx + 1}</span>
                      <span className="text-sm font-semibold text-text-primary">{ref.location_zh}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
                      {ref.atmosphere && (
                        <span>氛围 <span className="text-text-tertiary">{ref.atmosphere}</span></span>
                      )}
                      {ref.time_of_day && (
                        <span>时段 <span className="text-text-tertiary">{ref.time_of_day}</span></span>
                      )}
                      {ref.lighting_condition && (
                        <span>光照 <span className="text-text-tertiary">{ref.lighting_condition}</span></span>
                      )}
                    </div>
                  </div>

                  {/* T22-NEW-2: Image area — smart layout based on which URLs exist */}
                  {hasNone ? (
                    /* Edge case: neither interior nor exterior — unified error message */
                    <div className="flex flex-col items-center justify-center gap-3 py-10 px-4">
                      <ImageOff className="w-10 h-10 text-text-muted/40" />
                      <p className="text-sm text-text-muted text-center">场景图生成失败，请重新生成</p>
                      {!isLocked && (
                        <button
                          onClick={() => handleRegenerate(ref.location_id, "both")}
                          disabled={interiorRegenerating || exteriorRegenerating}
                          className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary hover:bg-brand-primary/25 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <RotateCcw className="w-3 h-3" />
                          重新生成场景图
                        </button>
                      )}
                    </div>
                  ) : (
                    /* At least one image exists — smart grid */
                    <>
                      <div className={gridClass}>
                        {/* Interior — only render slot if interior_url exists */}
                        {hasInterior && (
                          <div className="relative">
                            {/* Only show "内景" badge when both images present; single image needs no label */}
                            {hasBoth && (
                              <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-full bg-black/60 text-white text-[10px] font-medium">
                                内景
                              </div>
                            )}
                            <div className="relative aspect-[3/4] bg-bg-tertiary">
                              {interiorRegenerating ? (
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                  <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                                  <p className="text-xs text-text-muted">重新生成中...</p>
                                </div>
                              ) : !imgErrors[interiorErrKey] ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                  src={toAbsoluteUrl(ref.interior_url!) || ref.interior_url!}
                                  alt={`${ref.location_zh} 内景`}
                                  className="absolute inset-0 w-full h-full object-cover"
                                  onError={() => {
                                    // eslint-disable-next-line no-console
                                    console.warn("[SceneRefsPreview] interior img load error", ref.location_id);
                                    setImgErrors((prev) => ({ ...prev, [interiorErrKey]: true }));
                                  }}
                                />
                              ) : (
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                  <ImageOff className="w-10 h-10 text-text-muted/50" />
                                  <span className="text-text-muted/70 text-xs">图片加载失败</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Exterior — only render slot if exterior_url exists */}
                        {hasExterior && (
                          <div className={`relative${hasBoth ? " border-l border-white/5" : ""}`}>
                            {/* Only show "外景" badge when both images present */}
                            {hasBoth && (
                              <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-full bg-black/60 text-white text-[10px] font-medium">
                                外景
                              </div>
                            )}
                            <div className="relative aspect-[3/4] bg-bg-tertiary">
                              {exteriorRegenerating ? (
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                  <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                                  <p className="text-xs text-text-muted">重新生成中...</p>
                                </div>
                              ) : !imgErrors[exteriorErrKey] ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                  src={toAbsoluteUrl(ref.exterior_url!) || ref.exterior_url!}
                                  alt={`${ref.location_zh} 外景`}
                                  className="absolute inset-0 w-full h-full object-cover"
                                  onError={() => {
                                    // eslint-disable-next-line no-console
                                    console.warn("[SceneRefsPreview] exterior img load error", ref.location_id);
                                    setImgErrors((prev) => ({ ...prev, [exteriorErrKey]: true }));
                                  }}
                                />
                              ) : (
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                  <ImageOff className="w-10 h-10 text-text-muted/50" />
                                  <span className="text-text-muted/70 text-xs">图片加载失败</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* T22-NEW-2: Scene type label — only shown for single-image cases */}
                      {sceneTypeLabel && (
                        <div className="px-4 pt-2">
                          <span className="text-[11px] text-text-muted/60">{sceneTypeLabel}</span>
                        </div>
                      )}
                    </>
                  )}

                  {/* Description + action area */}
                  {!hasNone && (
                    <div className="p-4 space-y-3">
                      {!isEditingThis ? (
                        <>
                          <p className="text-sm text-text-tertiary leading-relaxed">
                            {ref.description_zh || `${ref.interior_description || ""} / ${ref.exterior_description || ""}`}
                          </p>
                          {/* D.14: hide action buttons when locked */}
                          {!isLocked && (
                            <div className="flex flex-wrap gap-2">
                              <button
                                onClick={() => handleEdit(ref.location_id, ref.interior_description || ref.exterior_description || ref.description_zh || "")}
                                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer"
                              >
                                <Pencil className="w-3 h-3" />
                                编辑描述
                              </button>
                              {/* T22-NEW-2: Only show "重生内景" when interior_url exists */}
                              {hasInterior && (
                                <button
                                  onClick={() => handleRegenerate(ref.location_id, "interior")}
                                  disabled={interiorRegenerating}
                                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  <RefreshCw className="w-3 h-3" />
                                  重生内景
                                </button>
                              )}
                              {/* T22-NEW-2: Only show "重生外景" when exterior_url exists */}
                              {hasExterior && (
                                <button
                                  onClick={() => handleRegenerate(ref.location_id, "exterior")}
                                  disabled={exteriorRegenerating}
                                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  <RefreshCw className="w-3 h-3" />
                                  重生外景
                                </button>
                              )}
                              {/* T22-NEW-2: "重生全部" → "重生此场景" when only one image */}
                              <button
                                onClick={() => handleRegenerate(ref.location_id, hasBoth ? "both" : hasInterior ? "interior" : "exterior")}
                                disabled={interiorRegenerating || exteriorRegenerating}
                                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary hover:bg-brand-primary/25 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <RotateCcw className="w-3 h-3" />
                                {hasBoth ? "重生全部" : "重生此场景"}
                              </button>
                            </div>
                          )}
                        </>
                      ) : (
                        // 编辑模式 — textarea + 应用按钮 (重生 with user_edit)
                        <div className="space-y-2">
                          <textarea
                            value={editInput}
                            onChange={(e) => setEditInput(e.target.value)}
                            placeholder="调整场景氛围描述, 例如: 'add neon signs in Chinese, more crowded'"
                            rows={3}
                            className="w-full px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50 resize-none"
                          />
                          <div className="flex flex-wrap gap-2">
                            {/* T22-NEW-2: edit mode — only show "应用并重生全部" when both exist */}
                            {hasBoth && (
                              <button
                                onClick={() => handleRegenerate(ref.location_id, "both", editInput)}
                                disabled={!editInput.trim() || interiorRegenerating || exteriorRegenerating}
                                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary hover:bg-brand-primary/25 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <RefreshCw className="w-3 h-3" />
                                应用并重生全部
                              </button>
                            )}
                            {hasInterior && (
                              <button
                                onClick={() => handleRegenerate(ref.location_id, "interior", editInput)}
                                disabled={!editInput.trim() || interiorRegenerating}
                                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {hasBoth ? "仅重生内景" : "应用并重生"}
                              </button>
                            )}
                            {hasExterior && (
                              <button
                                onClick={() => handleRegenerate(ref.location_id, "exterior", editInput)}
                                disabled={!editInput.trim() || exteriorRegenerating}
                                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {hasBoth ? "仅重生外景" : "应用并重生"}
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setEditingLocation(null);
                                setEditInput("");
                              }}
                              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-white/10 text-text-secondary hover:bg-white/5 transition-colors cursor-pointer"
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Confirm CTA */}
        {!isLocked && hasData && (
          <button
            onClick={handleConfirmWithApi}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3"
          >
            <Play className="w-4 h-4" />
            确认场景，继续生成画面
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </motion.div>
    </main>
  );
}
