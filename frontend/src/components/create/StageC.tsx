"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle2, AlertCircle, User, MapPin, ChevronRight, RotateCcw, Pencil, Play } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCreate } from "@/contexts/CreateContext";
import { mockShotGenProgress, mockPreviewCharacters, mockPreviewScenes } from "@/lib/mock-data";

const ADJUST_TAGS = ["换发色", "换服装", "更年轻", "更成熟", "换风格"];

export default function StageC() {
  const { state, dispatch } = useCreate();
  const router = useRouter();
  const cancelRef = useRef<(() => void) | null>(null);

  // Text generation phase (Stage 1-4) → then transition to char-preview
  useEffect(() => {
    if (state.generationSubPhase !== "text-gen") return;

    dispatch({ type: "START_GENERATION" });

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
      const step = steps[i];
      setTimeout(() => {
        if (!cancelled) {
          dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress: step.progress, message: step.message } });
          i++;
          run();
        }
      }, step.delay);
    };
    run();

    return () => { cancelled = true; };
  }, [state.generationSubPhase, dispatch]);

  // Shot generation phase — uses shot-only progress (no Stage 1-4 repeat)
  useEffect(() => {
    if (state.generationSubPhase !== "shot-gen") return;

    // Reset progress for shot phase start
    dispatch({ type: "START_GENERATION" });

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
  }, [state.generationSubPhase, dispatch]);

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

  // ============ Render based on sub-phase ============

  if (state.generationSubPhase === "char-preview") {
    return (
      <CharacterPreview
        characters={state.previewCharacters}
        onUpdateCharacter={(id, updates) => dispatch({ type: "UPDATE_PREVIEW_CHARACTER", payload: { id, updates } })}
        onConfirm={handleConfirmCharacters}
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

  // text-gen or shot-gen — progress UI
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
          {isError ? "生成遇到问题" : state.generationSubPhase === "shot-gen" ? "正在绘制画面" : "正在创作你的故事"}
        </h1>
        <p className="text-text-tertiary text-sm mb-8">
          {isError
            ? state.generationMessage
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

        {/* text-gen hint — only during text generation phase */}
        {state.generationSubPhase === "text-gen" && !isError && (
          <p className="text-text-tertiary text-xs mb-6">
            正在创作中，稍后需要你确认角色和场景哦～可以先喝杯可可，保持页面打开就好
          </p>
        )}

        {state.generationLog.length > 0 && (
          <div className="bg-bg-secondary rounded-xl p-4 border border-white/5 text-left max-h-48 overflow-y-auto">
            <div className="space-y-2">
              {state.generationLog.map((entry, i) => (
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

import type { PreviewCharacter } from "@/types/create";

function CharacterPreview({
  characters,
  onUpdateCharacter,
  onConfirm,
}: {
  characters: PreviewCharacter[];
  onUpdateCharacter: (id: string, updates: Partial<PreviewCharacter>) => void;
  onConfirm: () => void;
}) {
  const [countdown, setCountdown] = useState(10);
  const [paused, setPaused] = useState(false);
  const [adjustingId, setAdjustingId] = useState<string | null>(null);
  const [adjustInput, setAdjustInput] = useState("");
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
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

  const handleAdjust = (charId: string) => {
    setPaused(true);
    setAdjustingId(charId);
    setAdjustInput("");
  };

  const handleRegenerate = (charId: string) => {
    setRegeneratingId(charId);
    setTimeout(() => setRegeneratingId(null), 2000);
  };

  const handleApplyAdjustment = (charId: string) => {
    if (adjustInput.trim()) {
      const char = characters.find((c) => c.id === charId);
      if (char) {
        onUpdateCharacter(charId, { adjustments: [...char.adjustments, adjustInput.trim()] });
      }
    }
    handleRegenerate(charId);
    setAdjustingId(null);
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto"
      >
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
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">
                {countdown}
              </div>
              <span className="text-xs text-text-muted">秒后自动继续</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {characters.map((char) => (
            <motion.div
              key={char.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden"
            >
              <div className="relative aspect-[3/4] bg-bg-tertiary">
                {regeneratingId === char.id ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                  </div>
                ) : (
                  <Image src={char.fullbodyUrl} alt={char.name} fill className="object-cover" sizes="300px" />
                )}
                <button
                  onClick={() => handleRegenerate(char.id)}
                  className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-colors cursor-pointer"
                  title="重新生成"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="p-3">
                <p className="font-semibold text-text-primary text-sm mb-0.5">{char.name}</p>
                <p className="text-text-muted text-xs mb-2 line-clamp-2">{char.description}</p>
                <button
                  onClick={() => handleAdjust(char.id)}
                  className="flex items-center gap-1 text-xs text-brand-primary hover:underline cursor-pointer"
                >
                  <Pencil className="w-3 h-3" />
                  调整
                </button>
              </div>

              <AnimatePresence>
                {adjustingId === char.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/5 overflow-hidden"
                  >
                    <div className="p-3 space-y-2">
                      <div className="flex flex-wrap gap-1.5">
                        {ADJUST_TAGS.map((tag) => (
                          <button
                            key={tag}
                            onClick={() => setAdjustInput(tag)}
                            className="px-2.5 py-1 rounded-full bg-bg-tertiary text-text-secondary text-xs hover:bg-brand-primary/10 hover:text-brand-primary transition-colors cursor-pointer"
                          >
                            {tag}
                          </button>
                        ))}
                      </div>
                      <input
                        type="text"
                        value={adjustInput}
                        onChange={(e) => setAdjustInput(e.target.value)}
                        placeholder="我想让她穿红色连衣裙"
                        className="w-full px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-xs placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApplyAdjustment(char.id)}
                          className="flex-1 py-1.5 rounded-lg bg-brand-primary/15 text-brand-primary text-xs font-medium cursor-pointer"
                        >
                          重新生成
                        </button>
                        <button
                          onClick={() => setAdjustingId(null)}
                          className="flex-1 py-1.5 rounded-lg border border-white/10 text-text-secondary text-xs cursor-pointer"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        <button
          onClick={onConfirm}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3"
        >
          确认角色，继续
          <ChevronRight className="w-4 h-4" />
        </button>
      </motion.div>
    </main>
  );
}

// ============ Scene Preview Checkpoint ============

import type { PreviewScene } from "@/types/create";

function ScenePreview({
  scenes,
  onUpdateScene,
  onConfirm,
}: {
  scenes: PreviewScene[];
  onUpdateScene: (id: string, userEdit: string) => void;
  onConfirm: () => void;
}) {
  const [countdown, setCountdown] = useState(10);
  const [paused, setPaused] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto"
      >
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
              <div className="w-9 h-9 rounded-full border-2 border-brand-primary/50 flex items-center justify-center text-brand-primary text-sm font-bold">
                {countdown}
              </div>
              <span className="text-xs text-text-muted">秒后自动继续</span>
            </div>
          )}
        </div>

        <div className="space-y-3 mb-6">
          {scenes.map((scene, idx) => (
            <motion.div
              key={scene.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-bg-secondary rounded-xl border border-white/5 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-brand-primary font-medium">场景 {idx + 1}</span>
                    <span className="text-sm font-semibold text-text-primary">{scene.name}</span>
                  </div>
                  {editingId === scene.id ? (
                    <textarea
                      value={scene.userEdit || scene.description}
                      onChange={(e) => onUpdateScene(scene.id, e.target.value)}
                      placeholder="描述你想要的场景氛围"
                      rows={3}
                      className="w-full mt-2 px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand-primary/50 resize-none"
                    />
                  ) : (
                    <p className="text-text-tertiary text-sm leading-relaxed">{scene.userEdit || scene.description}</p>
                  )}
                </div>
                {editingId === scene.id ? (
                  <button
                    onClick={() => setEditingId(null)}
                    className="text-xs text-brand-primary hover:underline mt-1 flex-shrink-0 cursor-pointer"
                  >
                    完成
                  </button>
                ) : (
                  <button
                    onClick={() => handleEdit(scene.id)}
                    className="flex items-center gap-1 text-xs text-text-muted hover:text-brand-primary transition-colors mt-1 flex-shrink-0 cursor-pointer"
                  >
                    <Pencil className="w-3 h-3" />
                    修改
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        <button
          onClick={onConfirm}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3"
        >
          <Play className="w-4 h-4" />
          开始绘制
        </button>
      </motion.div>
    </main>
  );
}
