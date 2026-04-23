"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle2, AlertCircle, User, MapPin, ChevronRight, RotateCcw, Pencil, Play } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCreate } from "@/contexts/CreateContext";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { mockShotGenProgress, mockPreviewCharacters, mockPreviewScenes } from "@/lib/mock-data";
import type { PreviewCharacter, PreviewScene, Shot } from "@/types/create";

const ADJUST_TAGS = ["换发色", "换服装", "更年轻", "更成熟", "换风格"];

// RF-3: Fixed cocoa tip (always shown, not in carousel)
const FIXED_TIP = "稍后需要你确认角色和场景哦～可以先喝杯可可，保持页面打开就好";

// RF-3: 19 carousel tips (9 original + 10 new, without cocoa)
const CAROUSEL_TIPS = [
  // Original product tips (4, cocoa removed)
  "你知道吗？序话支持 28 种视觉风格，从写实到水墨都有",
  "角色预览时，你可以调整角色的发色、服装和年龄",
  "场景确认环节，你可以修改每个场景的氛围描述",
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

// FE-1: Map backend stage name → user-facing phase label. Covers all
// Pipeline stages (see pipeline_orchestrator.py progress_callback calls).
const STAGE_LABEL: Record<string, string> = {
  story_generation: "正在编写剧本...",
  character_design: "正在设计角色...",
  character_ready: "正在设计角色...",
  screenplay: "正在编写剧本...",
  storyboard: "正在创建分镜...",
  image_generation: "正在绘制画面...",
  bgm: "正在谱曲...",
  music: "正在谱曲...",
};

function resolvePhaseTitle(isError: boolean, subPhase: string, stage: string | null | undefined): string {
  if (isError) return "生成遇到问题";
  // Prefer backend stage when available (FE-1)
  if (stage && STAGE_LABEL[stage]) {
    // Remove trailing ellipsis for use as a heading
    return STAGE_LABEL[stage].replace(/\.+$/, "");
  }
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

  // F-1: Carousel tip state — random start index
  const [tipIndex, setTipIndex] = useState(() => Math.floor(Math.random() * CAROUSEL_TIPS.length));

  // F-2: Start time ref for time estimation
  const startTimeRef = useRef<number>(Date.now());

  // RF-4: Backend estimated remaining seconds
  const backendEstimatedSecondsRef = useRef<number | null>(null);

  // F-2 (R3): Simulated early progress ref — advances 1% per 12s up to 5%, prevents "0% stuck" perception
  const simulatedProgressRef = useRef(0);
  const simulatedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // F-3: Consecutive error counters for both polling effects
  const textGenErrorCount = useRef(0);
  const shotGenErrorCount = useRef(0);
  const [showRetryHint, setShowRetryHint] = useState(false);

  // FE-1: Track current backend stage for precise phase title mapping
  const [currentStage, setCurrentStage] = useState<string | null>(null);

  const token = getStoredToken();
  const projectId = state.projectId;
  const useRealApi = !!(isLoggedIn && token && projectId);

  const clearPoll = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  // F-1: Carousel timer — 8 second rotation
  useEffect(() => {
    const isGenerating = (state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen")
      && state.generationStatus !== "error";
    if (!isGenerating) return;

    const interval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % CAROUSEL_TIPS.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [state.generationSubPhase, state.generationStatus]);

  // F-2: Reset start time when entering a new generation sub-phase
  useEffect(() => {
    if (state.generationSubPhase === "text-gen" || state.generationSubPhase === "shot-gen") {
      startTimeRef.current = Date.now();
    }
  }, [state.generationSubPhase]);

  // RF-4: Compute estimated remaining minutes — prefer backend value, fallback to linear extrapolation
  const estimatedMinutes = (() => {
    // RF-4: If backend provides estimated_remaining_seconds, use it
    const backendSec = backendEstimatedSecondsRef.current;
    if (backendSec !== null && backendSec > 0) {
      const minutes = Math.ceil(backendSec / 60);
      return minutes > 0 ? Math.min(minutes, 20) : null;
    }
    // Fallback: linear extrapolation
    const progress = state.generationProgress;
    if (progress < 10) return null; // 等 Stage 2 完成（10%）后再显示，避免低进度线性外推发散
    const elapsed = (Date.now() - startTimeRef.current) / 1000; // seconds
    if (elapsed < 5) return null;
    const totalEstimated = elapsed / (progress / 100);
    const remaining = totalEstimated - elapsed;
    const minutes = Math.ceil(remaining / 60);
    return minutes > 0 ? Math.min(minutes, 20) : null; // 上限 20 分钟
  })();

  // F-2: Checkpoint preview messages
  const checkpointPreview = (() => {
    const progress = state.generationProgress;
    if (progress >= 55 && progress <= 63) return "即将到达角色预览检查点";
    return null;
  })();

  useEffect(() => { return () => clearPoll(); }, [clearPoll]);

  // ============ Text-gen phase ============
  useEffect(() => {
    if (state.generationSubPhase !== "text-gen") return;
    dispatch({ type: "START_GENERATION" });

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

    pollRef.current = setInterval(async () => {
      try {
        const status = await apiFetch<{ status: string; stage: string; progress: number; message: string; estimated_remaining_seconds?: number }>(
          `/projects/${projectId}/chapters/1/status`, {}, token
        );
        textGenErrorCount.current = 0; // F-3: reset on success
        setShowRetryHint(false);

        // FE-1: capture backend stage for title mapping
        if (status.stage) setCurrentStage(status.stage);

        // RF-4: Store backend estimated remaining seconds
        if (status.estimated_remaining_seconds !== undefined && status.estimated_remaining_seconds > 0) {
          backendEstimatedSecondsRef.current = status.estimated_remaining_seconds;
        } else {
          backendEstimatedSecondsRef.current = null;
        }

        // FE-3: Trust real backend progress once any value > 0 comes in. Only use
        // the simulated value when backend is still at 0 (early startup).
        const effectiveProgress = status.progress > 0 ? status.progress : simulatedProgressRef.current;
        // Once real progress exceeds 5%, stop the simulated timer
        if (status.progress >= 5 && simulatedTimerRef.current) {
          clearInterval(simulatedTimerRef.current);
          simulatedTimerRef.current = null;
        }

        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: effectiveProgress, message: status.message } });

        // RF-6: Transition to char-preview when Stage 2 completes (character_ready) or fallback to completed
        if (status.stage === "character_ready" || status.status === "completed") {
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          // Use real outline data for character/scene previews
          const chars: PreviewCharacter[] = state.outline?.characters?.map(c => ({
            id: c.id, name: c.name, description: c.description,
            fullbodyUrl: "/brand/logo-48.png", adjustments: [],
          })) || mockPreviewCharacters;
          // F-3 (R3): Prefer description_zh (Chinese) if available, fallback to description (English)
          const scenes: PreviewScene[] = state.outline?.scenes?.map(s => ({
            id: s.id, name: s.name, description: s.description_zh || s.description, userEdit: "",
          })) || mockPreviewScenes;
          dispatch({ type: "SET_PREVIEW_CHARACTERS", payload: chars });
          dispatch({ type: "SET_PREVIEW_SCENES", payload: scenes });
          dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "char-preview" });
        }

        if (status.status === "failed") {
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          dispatch({ type: "GENERATION_ERROR", payload: status.message || "生成失败" });
        }
      } catch {
        // F-3: Consecutive error handling
        textGenErrorCount.current++;
        if (textGenErrorCount.current >= 3) setShowRetryHint(true);
        if (textGenErrorCount.current >= 15) {
          clearPoll();
          if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
          dispatch({ type: "GENERATION_ERROR", payload: "服务器连接异常，请稍后刷新页面重试" });
        }
      }
    }, 2000);

    return () => {
      clearPoll();
      if (simulatedTimerRef.current) { clearInterval(simulatedTimerRef.current); simulatedTimerRef.current = null; }
    };
  }, [state.generationSubPhase, dispatch, useRealApi, token, projectId, state.outline, clearPoll]);

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
    completedRef.current = false;

    // FE-5: Robust completion handler. Accepts both `status === "completed"` and
    // `progress >= 100` as triggers. Fetches /generation-result and transitions
    // to preview. Includes console timing for observability.
    const finalizeAndGoToPreview = async () => {
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
            narration?: string;
            narrationSegment?: string;
            textOverlay?: { type: string; text: string };
            shotType?: string;
            cameraAngle?: string;
            sceneId?: number;
          }> } | null;
          totalShots: number;
        }>(`/projects/${projectId}/generation-result`, {}, token);
        // eslint-disable-next-line no-console
        console.timeEnd("[FE-5] /generation-result roundtrip");

        if (result.storyboard?.shots?.length) {
          const mappedShots: Shot[] = result.storyboard.shots.map((s) => ({
            shotId: s.shotId,
            sceneId: s.sceneId || 1,
            imagePrompt: "",
            narrationSegment: s.narrationSegment || s.narration || "",
            shotType: s.shotType || "medium shot",
            cameraAngle: s.cameraAngle || "eye level",
            textType: s.textOverlay?.type || "narration",
            chineseText: s.textOverlay?.text ? [s.textOverlay.text] : [],
            imageUrl: s.imageUrl,
            charactersInScene: [],
          }));
          dispatch({ type: "GENERATION_COMPLETE", payload: mappedShots });
        } else {
          dispatch({ type: "GENERATION_COMPLETE", payload: [] });
        }
        dispatch({ type: "SET_STAGE", payload: "preview" });
      } catch {
        // eslint-disable-next-line no-console
        console.timeEnd("[FE-5] /generation-result roundtrip");
        dispatch({ type: "GENERATION_ERROR", payload: "加载生成结果失败" });
      }
    };

    pollRef.current = setInterval(async () => {
      try {
        const status = await apiFetch<{ status: string; stage: string; progress: number; message: string; estimated_remaining_seconds?: number }>(
          `/projects/${projectId}/chapters/1/status`, {}, token
        );
        shotGenErrorCount.current = 0; // F-3: reset on success
        setShowRetryHint(false);

        // FE-1: capture backend stage for title mapping
        if (status.stage) setCurrentStage(status.stage);

        // RF-4: Store backend estimated remaining seconds
        if (status.estimated_remaining_seconds !== undefined && status.estimated_remaining_seconds > 0) {
          backendEstimatedSecondsRef.current = status.estimated_remaining_seconds;
        } else {
          backendEstimatedSecondsRef.current = null;
        }

        // FE-3: Trust backend progress directly in shot-gen (no simulated clamp)
        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: status.progress, message: status.message } });

        // FE-5: Broaden completion trigger. Previously the branch only fired
        // on `status === "completed"`. If the backend briefly set progress=100
        // while `status` was still `processing`, the user would see "100%"
        // with no transition until the next poll tick + status flip.
        if (status.status === "completed" || status.progress >= 100) {
          await finalizeAndGoToPreview();
          return;
        }

        if (status.status === "failed") {
          clearPoll();
          dispatch({ type: "GENERATION_ERROR", payload: status.message || "生成失败" });
        }
      } catch {
        // F-3: Consecutive error handling
        shotGenErrorCount.current++;
        if (shotGenErrorCount.current >= 3) setShowRetryHint(true);
        if (shotGenErrorCount.current >= 15) {
          clearPoll();
          dispatch({ type: "GENERATION_ERROR", payload: "服务器连接异常，请稍后刷新页面重试" });
        }
      }
    }, 2000);

    return () => clearPoll();
  }, [state.generationSubPhase, dispatch, useRealApi, token, projectId, clearPoll]);

  // ============ Handlers ============
  const handleConfirmCharacters = useCallback(() => {
    dispatch({ type: "CONFIRM_CHARACTERS" });
    dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "scene-preview" });
  }, [dispatch]);

  const handleConfirmScenes = useCallback(() => {
    dispatch({ type: "CONFIRM_SCENES" });
    dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "shot-gen" });
  }, [dispatch]);

  const handleBackgroundGenerate = () => {
    router.push("/dashboard");
  };

  const isError = state.generationStatus === "error";

  // ============ Render ============
  if (state.generationSubPhase === "char-preview") {
    return (
      <CharacterPreview
        characters={state.previewCharacters}
        onUpdateCharacter={(id, updates) => dispatch({ type: "UPDATE_PREVIEW_CHARACTER", payload: { id, updates } })}
        onConfirm={handleConfirmCharacters}
        projectId={projectId}
        token={token}
      />
    );
  }

  if (state.generationSubPhase === "scene-preview") {
    return (
      <ScenePreview
        scenes={state.previewScenes}
        onUpdateScene={(id, userEdit) => dispatch({ type: "UPDATE_PREVIEW_SCENE", payload: { id, userEdit } })}
        onConfirm={handleConfirmScenes}
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
        <p className="text-text-tertiary text-sm mb-8">
          {isError
            ? friendlyError(state.generationMessage)
            : state.generationSubPhase === "shot-gen"
              ? "AI 正在逐张绘制画面，可以选择后台生成"
              : "AI 正在全力创作，请耐心等待"}
        </p>

        {!isError && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-muted">进度</span>
              <span className="text-xs text-text-muted">{state.generationProgress}%</span>
            </div>
            <div className="w-full h-2 bg-bg-secondary rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-brand-primary to-purple-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${state.generationProgress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
            {/* F-2: Estimated remaining time / R5-2: show "即将完成" when progress >= 100 */}
            {state.generationProgress >= 100 ? (
              <p className="text-xs text-text-muted mt-2">即将完成</p>
            ) : estimatedMinutes !== null && (
              <p className="text-xs text-text-muted mt-2">
                预计还需约 {estimatedMinutes} 分钟
              </p>
            )}
            {/* R4-3: Cocoa tip only shown during text-gen phase (before character_ready), not during shot-gen */}
            {state.generationSubPhase === "text-gen" && (
              <p className="text-xs text-text-tertiary mt-3 opacity-80">
                {FIXED_TIP}
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
            {state.generationMessage}
          </motion.p>
        )}

        {/* F-2: Checkpoint preview */}
        {!isError && checkpointPreview && (
          <motion.p
            key={checkpointPreview}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-amber-400 mb-4 font-medium"
          >
            {checkpointPreview}
          </motion.p>
        )}

        {/* F-3: Network retry indicator (3-14 consecutive errors) */}
        {!isError && showRetryHint && (
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
                  <span className="text-text-tertiary">{entry.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {state.generationSubPhase === "shot-gen" && !isError && (
          <button
            onClick={handleBackgroundGenerate}
            className="mt-6 py-2.5 px-6 rounded-lg border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors cursor-pointer"
          >
            后台生成，去做别的
          </button>
        )}

        {isError && (
          <button
            onClick={() => dispatch({ type: "SET_STAGE", payload: "confirm" })}
            className="btn-primary mt-6 px-8"
          >
            返回重试
          </button>
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
  const [countdown, setCountdown] = useState(20); // R6-4: 20s countdown
  const [paused, setPaused] = useState(false);
  const [adjustingId, setAdjustingId] = useState<string | null>(null);
  const [adjustInput, setAdjustInput] = useState("");
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
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
  }, [projectId, token, onConfirm, clearTimer]);

  useEffect(() => {
    if (paused) { clearTimer(); return; }
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) { clearTimer(); handleConfirmWithApi(); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearTimer();
  }, [paused, handleConfirmWithApi, clearTimer]);

  const handleAdjust = (charId: string) => {
    setPaused(true);
    setAdjustingId(charId);
    setAdjustInput("");
  };

  const handleRegenerate = (charId: string) => {
    setRegeneratingId(charId);
    setTimeout(() => setRegeneratingId(null), 2000);
  };

  // RF-5: Real API for character adjustment with mock fallback
  const handleApplyAdjustment = async (charId: string) => {
    if (!adjustInput.trim()) {
      setAdjustingId(null);
      return;
    }

    setRegeneratingId(charId);

    try {
      // Try real API
      // F-1 fix: Backend returns { success, character: { description, description_zh, physical, clothing, ... }, char_id, message }
      const result = await apiFetch<{ success: boolean; character: { description?: string; description_zh?: string }; char_id: string; message: string }>(
        `/projects/${projectId}/characters/${charId}/adjust`,
        { method: "POST", body: JSON.stringify({ adjustment: adjustInput.trim() }) },
        token
      );
      // Success: update character with new description from nested character object
      const char = characters.find((c) => c.id === charId);
      if (char) {
        onUpdateCharacter(charId, {
          description: result.character?.description_zh || result.character?.description || char.description,
          adjustments: [...char.adjustments, adjustInput.trim()],
        });
      }
    } catch {
      // R4-2: Clear loading state on failure + show error toast
      setRegeneratingId(null);
      setAdjustingId(null);
      toast("error", "调整失败，请重试");
      return;
    }

    setRegeneratingId(null);
    setAdjustingId(null);
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <User className="w-5 h-5 text-brand-primary" />
              <h1 className="text-xl font-bold">角色预览</h1>
            </div>
            <p className="text-text-tertiary text-sm">确认角色外观，或调整后继续</p>
          </div>
          {!paused && (
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">{countdown}</div>
              <span className="text-xs text-text-muted">秒后自动继续</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {characters.map((char) => (
            <motion.div key={char.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden">
              <div className="relative aspect-[3/4] bg-bg-tertiary">
                {regeneratingId === char.id ? (
                  <div className="absolute inset-0 flex items-center justify-center"><Loader2 className="w-8 h-8 text-brand-primary animate-spin" /></div>
                ) : (
                  <Image src={char.fullbodyUrl} alt={char.name} fill className="object-cover" sizes="300px" />
                )}
                <button onClick={() => handleRegenerate(char.id)} className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-colors cursor-pointer" title="重新生成">
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="p-3">
                <p className="font-semibold text-text-primary text-sm mb-0.5">{char.name}</p>
                <p className="text-text-muted text-xs mb-2 line-clamp-2">{char.description}</p>
                <button onClick={() => handleAdjust(char.id)} className="flex items-center gap-1 text-xs text-brand-primary hover:underline cursor-pointer"><Pencil className="w-3 h-3" />调整</button>
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
                      <input type="text" value={adjustInput} onChange={(e) => setAdjustInput(e.target.value)} placeholder="我想让她穿红色连衣裙" className="w-full px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-xs placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50" />
                      <div className="flex gap-2">
                        <button onClick={() => handleApplyAdjustment(char.id)} className="flex-1 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary text-xs font-medium cursor-pointer">重新生成</button>
                        <button onClick={() => setAdjustingId(null)} className="flex-1 py-1.5 rounded-lg border border-white/10 text-text-secondary text-xs cursor-pointer">取消</button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        <button onClick={handleConfirmWithApi} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
          确认角色，继续<ChevronRight className="w-4 h-4" />
        </button>
      </motion.div>
    </main>
  );
}

// ============ Scene Preview Checkpoint ============

function ScenePreview({
  scenes,
  onUpdateScene,
  onConfirm,
}: {
  scenes: PreviewScene[];
  onUpdateScene: (id: string, userEdit: string) => void;
  onConfirm: () => void;
}) {
  const [countdown, setCountdown] = useState(20); // R6-4: 20s countdown
  const [paused, setPaused] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  useEffect(() => {
    if (paused) { clearTimer(); return; }
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) { clearTimer(); onConfirm(); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearTimer();
  }, [paused, onConfirm, clearTimer]);

  const handleEdit = (sceneId: string) => {
    setPaused(true);
    setEditingId(sceneId);
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-5 h-5 text-brand-primary" />
              <h1 className="text-xl font-bold">场景确认</h1>
            </div>
            <p className="text-text-tertiary text-sm">确认场景描述，或修改后开始绘制</p>
          </div>
          {!paused && (
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">{countdown}</div>
              <span className="text-xs text-text-muted">秒后自动继续</span>
            </div>
          )}
        </div>

        <div className="space-y-3 mb-6">
          {scenes.map((scene, idx) => (
            <motion.div key={scene.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="bg-bg-secondary rounded-xl border border-white/5 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-brand-primary font-medium">场景 {idx + 1}</span>
                    <span className="text-sm font-semibold text-text-primary">{scene.name}</span>
                  </div>
                  {editingId === scene.id ? (
                    <textarea value={scene.userEdit || scene.description} onChange={(e) => onUpdateScene(scene.id, e.target.value)} placeholder="描述你想要的场景氛围" rows={3} className="w-full mt-2 px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50 resize-none" />
                  ) : (
                    <p className="text-text-tertiary text-sm leading-relaxed">{scene.userEdit || scene.description}</p>
                  )}
                </div>
                {editingId === scene.id ? (
                  <button onClick={() => setEditingId(null)} className="text-xs text-brand-primary hover:underline mt-1 flex-shrink-0 cursor-pointer">完成</button>
                ) : (
                  <button onClick={() => handleEdit(scene.id)} className="flex items-center gap-1 text-xs text-text-muted hover:text-brand-primary transition-colors mt-1 flex-shrink-0 cursor-pointer"><Pencil className="w-3 h-3" />修改</button>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        <button onClick={onConfirm} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
          <Play className="w-4 h-4" />开始绘制
        </button>
      </motion.div>
    </main>
  );
}
