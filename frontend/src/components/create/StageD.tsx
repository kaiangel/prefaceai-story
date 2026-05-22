"use client";

import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Trash2,
  Check,
  Image as ImageIcon,
  Sparkles,
  Loader2,
  Wand2,
  AlertTriangle,
  XCircle,
  RotateCcw,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCreate } from "@/contexts/CreateContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";
import BgmPlayer from "./BgmPlayer";
import { useToast } from "@/components/ui/Toast";

export default function StageD() {
  const { state, dispatch } = useCreate();
  const { toast } = useToast();
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [editingShotId, setEditingShotId] = useState<number | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [adjustmentText, setAdjustmentText] = useState("");
  const [adjusting, setAdjusting] = useState(false);
  // B44: whether safety_advice detail panel is expanded for current shot
  const [expandedSafety, setExpandedSafety] = useState<Record<number, boolean>>({});
  // D.17: ref for adjustment input to focus when user clicks "改一下文字"
  const adjustInputRef = useRef<HTMLInputElement>(null);

  const token = getStoredToken();
  const shots = state.shots;
  const currentShot = shots[currentIndex];

  // B46: compute failed shots (image_url === null and success !== true)
  const failedShotIndices: number[] = shots
    .map((s, i) => (s.imageUrl === null ? i : -1))
    .filter((i) => i !== -1);
  const failedShotCount = failedShotIndices.length;

  // B46: jump to the first failed shot
  const jumpToFirstFailedShot = useCallback(() => {
    if (failedShotIndices.length > 0) {
      setCurrentIndex(failedShotIndices[0]);
      // eslint-disable-next-line no-console
      console.log("[B46] jumping to first failed shot index=", failedShotIndices[0], "shotId=", shots[failedShotIndices[0]]?.shotId);
    }
  }, [failedShotIndices, shots]);

  // [StageD] Log #1 — render: how many shots, current index, projectId
  // eslint-disable-next-line no-console
  console.log("[StageD] render: projectId=", state.projectId, "shots.length=", shots.length, "failedShotCount=", failedShotCount, "currentIndex=", currentIndex, "currentShot.shotId=", currentShot?.shotId ?? "none", "bgmPlayer.status=", state.bgmPlayer.status, "bgmUrl=", state.bgmPlayer.bgmUrl?.slice(0, 60) ?? "null");

  if (!currentShot) {
    // [StageD] Log #2 — no shots at all (empty state) — possibly loading or pipeline failed
    // eslint-disable-next-line no-console
    console.warn("[StageD] currentShot is null — shots.length=", shots.length, "— likely empty generation result or hydration not complete");

    // RISK-T16-7: Show failed state UI instead of blank screen.
    // This happens when: (a) pipeline failed and storyboard_json is empty {},
    // or (b) status=completed but shots array is empty.
    const errorMessage = state.generationMessage
      ? state.generationMessage
      : "故事生成遇到了问题，画面数据为空。请返回重新创建。";

    return (
      <main className="container-lg py-16 pb-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg mx-auto text-center"
        >
          <div className="mb-8">
            <XCircle className="w-16 h-16 text-red-400 mx-auto" />
          </div>
          <h1 className="text-2xl font-bold mb-3 text-text-primary">
            故事生成遇到问题
          </h1>
          <p className="text-text-tertiary text-sm mb-6 leading-relaxed">
            {errorMessage}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => router.push("/create")}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-primary text-white font-medium hover:bg-brand-primary/90 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              重新创建故事
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-bg-secondary border border-white/10 text-text-secondary font-medium hover:bg-bg-tertiary transition-colors"
            >
              返回工作台
            </button>
          </div>
          <p className="text-text-muted text-xs mt-6">
            如果问题持续出现，请联系我们的支持团队
          </p>
        </motion.div>
      </main>
    );
  }

  const handlePrev = () => setCurrentIndex((i) => Math.max(0, i - 1));
  const handleNext = () => setCurrentIndex((i) => Math.min(shots.length - 1, i + 1));

  // B21: Ensure imageUrl bypasses browser disk cache after regeneration.
  // If backend already appended ?v=<timestamp> we use it as-is; otherwise we add one.
  const bustCache = (url: string): string => {
    if (!url) return url;
    return url.includes("?v=") ? url : `${url}?v=${Date.now()}`;
  };

  // KI-001: Regenerate shot — call POST API then update imageUrl
  const handleRegenerate = async (shotId: number) => {
    // [StageD] Log #3 — regenerate shot start
    // eslint-disable-next-line no-console
    console.log("[StageD] handleRegenerate: shotId=", shotId, "projectId=", state.projectId);
    setRegeneratingId(shotId);
    dispatch({ type: "REGENERATE_SHOT", payload: shotId });
    try {
      const result = await apiFetch<{
        status: string;
        imageUrl: string;
        shot_id: number;
      }>(
        `/projects/${state.projectId}/chapters/1/shots/${shotId}/regenerate`,
        { method: "POST" },
        token
      );
      // B21: apply cache-bust so the browser fetches the new image instead of
      // serving the old one from disk cache.
      const freshUrl = bustCache(result.imageUrl);
      // [StageD] Log #4 — regenerate success
      // eslint-disable-next-line no-console
      console.log("[StageD] handleRegenerate: SUCCESS shotId=", shotId, "newImageUrl=", freshUrl?.slice(0, 80) ?? "null");
      dispatch({
        type: "REGENERATE_SHOT_SUCCESS",
        payload: { shotId, imageUrl: freshUrl },
      });
      toast("success", "已重新生成");
    } catch (e) {
      // [StageD] Log #5 — regenerate error
      // eslint-disable-next-line no-console
      console.error("[StageD] handleRegenerate: ERROR shotId=", shotId, e instanceof Error ? e.message : e);
      toast("error", "重新生成失败，请重试");
    } finally {
      setRegeneratingId(null);
    }
  };

  // Adjust shot image — user provides Chinese intent, backend uses Haiku to modify image_prompt then regenerate
  const handleAdjust = async () => {
    if (!adjustmentText.trim()) return;
    // [StageD] Log #6 — adjust shot start
    // eslint-disable-next-line no-console
    console.log("[StageD] handleAdjust: shotId=", currentShot.shotId, "intent=", adjustmentText.trim().slice(0, 60));
    setAdjusting(true);
    dispatch({ type: "REGENERATE_SHOT", payload: currentShot.shotId });
    try {
      const result = await apiFetch<{
        status: string;
        imageUrl: string;
        shot_id: number;
        prompt_modified: boolean;
      }>(
        `/projects/${state.projectId}/chapters/1/shots/${currentShot.shotId}/regenerate`,
        {
          method: "POST",
          body: JSON.stringify({ adjustment_intent: adjustmentText.trim() }),
        },
        token
      );
      // B21: same cache-bust applied for adjustment-driven regeneration
      const freshUrl = bustCache(result.imageUrl);
      // [StageD] Log #7 — adjust success
      // eslint-disable-next-line no-console
      console.log("[StageD] handleAdjust: SUCCESS shotId=", currentShot.shotId, "prompt_modified=", result.prompt_modified, "newUrl=", freshUrl?.slice(0, 80) ?? "null");
      dispatch({
        type: "REGENERATE_SHOT_SUCCESS",
        payload: { shotId: currentShot.shotId, imageUrl: freshUrl },
      });
      toast("success", "画面已调整");
      setAdjustmentText("");
    } catch (e) {
      // [StageD] Log #8 — adjust error
      // eslint-disable-next-line no-console
      console.error("[StageD] handleAdjust: ERROR shotId=", currentShot.shotId, e instanceof Error ? e.message : e);
      toast("error", "调整失败，请重试");
    } finally {
      setAdjusting(false);
    }
  };

  // KI-002: Save edited text overlay (chinese_text) — call PATCH API to persist to DB
  const handleSaveEdit = async () => {
    if (!editingShotId) return;
    const shot = state.shots.find((s) => s.shotId === editingShotId);
    if (!shot) return;

    setSavingEdit(true);
    try {
      await apiFetch(
        `/projects/${state.projectId}/chapters/1/shots/${editingShotId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            chinese_text: shot.chineseText.join("\n"),
          }),
        },
        token
      );
      toast("success", "保存成功");
    } catch {
      toast("error", "保存失败，请重试");
    } finally {
      setSavingEdit(false);
      setEditingShotId(null);
    }
  };

  // KI-003: Delete shot — call DELETE API first, then remove from state
  const handleDelete = async (shotId: number) => {
    setDeletingId(shotId);
    try {
      await apiFetch(
        `/projects/${state.projectId}/chapters/1/shots/${shotId}`,
        { method: "DELETE" },
        token
      );
      dispatch({ type: "DELETE_SHOT", payload: shotId });
      if (currentIndex >= shots.length - 1 && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
      }
      toast("success", "已删除");
    } catch {
      toast("error", "删除失败，请重试");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeliver = () => {
    dispatch({ type: "SET_STAGE", payload: "deliver" });
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-3xl mx-auto"
      >
        {/* Title */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold mb-2">预览你的故事</h1>
          <p className="text-text-tertiary text-sm">
            浏览生成结果，可微调文字或重新生成不满意的画面
          </p>
        </div>

        {/* B46: Partial failure banner — shown when some shots failed to generate */}
        {failedShotCount > 0 && (
          <div className="mb-4 flex items-center justify-between gap-3 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 min-w-0">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <p className="text-red-300 text-sm">
                {shots.length - failedShotCount}/{shots.length} 张生成成功，{failedShotCount} 张未生成
              </p>
            </div>
            <button
              onClick={jumpToFirstFailedShot}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition-colors whitespace-nowrap"
            >
              查看并重生
            </button>
          </div>
        )}

        {/* Shot Navigator */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-text-muted">
            第 {currentIndex + 1} / {shots.length} 张
            {failedShotCount > 0 && (
              <span className="ml-2 text-red-400/80 text-xs">({failedShotCount} 张失败)</span>
            )}
          </span>
        </div>

        {/* Shot Card */}
        <div className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden mb-4">
          {/* Image Area */}
          <div className="bg-bg-primary flex items-center justify-center relative">
            <div className="w-full max-w-sm mx-auto aspect-[2/3]">
              {regeneratingId === currentShot.shotId || adjusting ? (
                <div className="w-full h-full flex flex-col items-center justify-center">
                  <Loader2 className="w-12 h-12 text-brand-primary/50 animate-spin mb-2" />
                  <span className="text-xs text-text-muted">
                    {adjusting ? "正在调整画面..." : "正在重新生成..."}
                  </span>
                </div>
              ) : toAbsoluteUrl(currentShot.imageUrl) ? (
                // P0-1: Use toAbsoluteUrl to convert /static/... paths to absolute backend URLs
                // P3-5: onError shows a fallback placeholder when image fails to load
                <img
                  src={toAbsoluteUrl(currentShot.imageUrl)!}
                  alt={`Shot ${currentShot.shotId}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.currentTarget;
                    target.style.display = "none";
                    const parent = target.parentElement;
                    if (parent && !parent.querySelector(".img-error-placeholder")) {
                      const div = document.createElement("div");
                      div.className = "img-error-placeholder w-full h-full flex flex-col items-center justify-center bg-bg-secondary";
                      div.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-text-muted/30 mb-2"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg><span style="font-size:12px;color:#6b7280">图像加载失败</span>`;
                      parent.appendChild(div);
                    }
                  }}
                />
              ) : (
                // B44: show structured safety advice when image generation failed
                <div className="w-full h-full flex flex-col items-center justify-center px-4 gap-2">
                  {currentShot.safetyAdvice ? (
                    // B44: structured safety advice from SafetyAdvisor
                    <>
                      <AlertTriangle className="w-10 h-10 text-amber-400/70 mb-1" />
                      <p className="text-xs font-medium text-amber-300 text-center">图生成失败</p>
                      <p className="text-[11px] text-amber-400/80 text-center leading-relaxed max-w-[200px]">
                        {currentShot.safetyAdvice.user_message}
                      </p>
                      <button
                        onClick={() => {
                          setExpandedSafety((prev) => ({ ...prev, [currentShot.shotId]: !prev[currentShot.shotId] }));
                        }}
                        className="mt-1 text-[10px] text-brand-primary/70 hover:text-brand-primary hover:underline"
                      >
                        {expandedSafety[currentShot.shotId] ? "收起详情" : "查看可疑词"}
                      </button>
                    </>
                  ) : currentShot.errorMessage ? (
                    <>
                      <ImageIcon className="w-12 h-12 text-text-muted/30 mb-1" />
                      <span className="text-xs text-amber-400/80 text-center leading-relaxed">
                        {currentShot.errorMessage}
                      </span>
                    </>
                  ) : (
                    <>
                      <ImageIcon className="w-12 h-12 text-text-muted/30 mb-1" />
                      <span className="text-xs text-text-muted">画面生成中...</span>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Nav Arrows */}
            <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-between px-2 pointer-events-none">
              <button
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="w-10 h-10 sm:w-8 sm:h-8 rounded-full bg-black/50 flex items-center justify-center text-white disabled:opacity-30 pointer-events-auto transition-opacity"
              >
                <ChevronLeft className="w-5 h-5 sm:w-4 sm:h-4" />
              </button>
              <button
                onClick={handleNext}
                disabled={currentIndex === shots.length - 1}
                className="w-10 h-10 sm:w-8 sm:h-8 rounded-full bg-black/50 flex items-center justify-center text-white disabled:opacity-30 pointer-events-auto transition-opacity"
              >
                <ChevronRight className="w-5 h-5 sm:w-4 sm:h-4" />
              </button>
            </div>
          </div>

          {/* Shot Info */}
          <div className="p-4 space-y-3">
            {/* Text Overlay (editable) — hidden when textType is "none" (empty shot) */}
            {currentShot.textType !== "none" && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-text-muted">画面文字</label>
                  {editingShotId === currentShot.shotId ? (
                    <button
                      onClick={handleSaveEdit}
                      disabled={savingEdit}
                      className="text-xs text-brand-primary flex items-center gap-1 disabled:opacity-50"
                    >
                      {savingEdit ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Check className="w-3 h-3" />
                      )}
                      {savingEdit ? "保存中..." : "完成"}
                    </button>
                  ) : (
                    <button
                      onClick={() => setEditingShotId(currentShot.shotId)}
                      className="text-xs text-text-muted hover:text-text-secondary"
                    >
                      编辑
                    </button>
                  )}
                </div>
                {editingShotId === currentShot.shotId ? (
                  <textarea
                    value={currentShot.chineseText.join("\n")}
                    onChange={(e) =>
                      dispatch({
                        type: "UPDATE_SHOT_TEXT",
                        payload: {
                          shotId: currentShot.shotId,
                          field: "chineseText",
                          value: e.target.value.split("\n"),
                        },
                      })
                    }
                    rows={3}
                    className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-2 text-text-primary text-sm resize-none focus:outline-none focus:border-brand-primary/50"
                  />
                ) : (
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {currentShot.chineseText.join("\n")}
                  </p>
                )}
              </div>
            )}

            {/* DEC-044 (2026-05-19): narration_segment 不再朗读为旁白, 仅作为画面描述使用.
                T20-21 重构后 narration_segment 会变短, 作为 caption / 画面描述 (read-only)
                展示给用户. 用户可通过上方"调整画面"按钮触发画面级编辑. */}
            {currentShot.narrationSegment && (
              <div>
                <label className="text-xs text-text-muted mb-1 block">描述（只读）</label>
                <p className="text-sm text-text-secondary/70 leading-relaxed">
                  {currentShot.narrationSegment}
                </p>
              </div>
            )}

            {/* Shot Meta */}
            <div className="flex items-center gap-3 text-[11px] sm:text-[10px] text-text-muted">
              <span>镜头: {currentShot.shotType}</span>
              <span>角度: {currentShot.cameraAngle}</span>
              <span>场景: {currentShot.sceneId}</span>
            </div>

            {/* B44: Safety advice panel — shown when image was blocked by content safety */}
            {!currentShot.imageUrl && currentShot.safetyAdvice && (
              <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 overflow-hidden">
                {/* Summary row — always visible */}
                <div className="flex items-start gap-2 p-3">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-amber-400/90 leading-relaxed">
                      {currentShot.safetyAdvice.user_message}
                    </p>
                    <button
                      onClick={() => setExpandedSafety((prev) => ({ ...prev, [currentShot.shotId]: !prev[currentShot.shotId] }))}
                      className="mt-1 text-[10px] text-amber-300/70 hover:text-amber-300 underline"
                    >
                      {expandedSafety[currentShot.shotId] ? "收起" : "查看可疑词和修改建议"}
                    </button>
                  </div>
                </div>
                {/* Expanded detail — suspected terms + suggested changes */}
                {expandedSafety[currentShot.shotId] && (
                  <div className="border-t border-amber-500/20 px-3 pb-3 pt-2 space-y-2">
                    {currentShot.safetyAdvice.suspected_terms.length > 0 && (
                      <div>
                        <p className="text-[10px] text-amber-400/60 mb-1 font-medium">可疑词</p>
                        <div className="flex flex-wrap gap-1">
                          {currentShot.safetyAdvice.suspected_terms.map((term, i) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">
                              {term}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {currentShot.safetyAdvice.suggested_changes.length > 0 && (
                      <div>
                        <p className="text-[10px] text-amber-400/60 mb-1 font-medium">建议替换</p>
                        <div className="space-y-0.5">
                          {currentShot.safetyAdvice.suggested_changes.map((change, i) => (
                            <p key={i} className="text-[10px] text-amber-300/80">
                              <span className="line-through text-amber-400/50">{change.original}</span>
                              <span className="mx-1 text-amber-400/40">→</span>
                              <span>{change.suggestion}</span>
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => {
                        if (currentShot.safetyAdvice) {
                          // Pre-fill adjustment input with suggested changes summary
                          const suggestions = currentShot.safetyAdvice.suggested_changes
                            .map((c) => `将"${c.original}"改为"${c.suggestion}"`)
                            .join("，");
                          setAdjustmentText(suggestions);
                          adjustInputRef.current?.focus();
                          adjustInputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
                        }
                      }}
                      className="w-full mt-1 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[10px] hover:bg-amber-500/30 transition-colors"
                    >
                      <Wand2 className="w-3 h-3" />
                      应用建议并重生成
                    </button>
                  </div>
                )}
              </div>
            )}
            {/* D.17 fallback: plain error message when no structured safety advice */}
            {!currentShot.imageUrl && !currentShot.safetyAdvice && currentShot.errorMessage && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-400/90 leading-relaxed">
                  {currentShot.errorMessage}
                </p>
              </div>
            )}

            {/* Adjust Image */}
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                <Wand2 className="w-3.5 h-3.5 text-brand-primary" />
                调整画面
              </div>
              <div className="flex gap-2">
                <input
                  ref={adjustInputRef}
                  type="text"
                  value={adjustmentText}
                  onChange={(e) => setAdjustmentText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.nativeEvent.isComposing) handleAdjust();
                  }}
                  placeholder='输入你想要的调整，如"让她笑"...'
                  disabled={adjusting || regeneratingId !== null}
                  className="flex-1 bg-bg-primary border border-white/10 rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-brand-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  onClick={handleAdjust}
                  disabled={adjusting || regeneratingId !== null || !adjustmentText.trim()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary/10 border border-brand-primary/30 text-brand-primary text-xs font-medium hover:bg-brand-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {adjusting ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Wand2 className="w-3 h-3" />
                  )}
                  {adjusting ? "调整中..." : "确认调整"}
                </button>
              </div>
              <p className="text-[10px] text-text-muted">
                提示：AI 会根据你的描述修改画面内容
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <div className="flex-1 flex flex-col">
                <button
                  onClick={() => handleRegenerate(currentShot.shotId)}
                  disabled={regeneratingId === currentShot.shotId || adjusting}
                  className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 text-text-muted hover:text-text-secondary hover:border-white/20 text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {regeneratingId === currentShot.shotId ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <RefreshCw className="w-3 h-3" />
                  )}
                  {regeneratingId === currentShot.shotId ? "生成中..." : "重新生成"}
                </button>
                <span className="text-[10px] text-text-muted text-center mt-1">
                  保持相同场景，产生不同构图变化
                </span>
              </div>
              <button
                onClick={() => handleDelete(currentShot.shotId)}
                disabled={deletingId === currentShot.shotId || adjusting || regeneratingId !== null}
                className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg border border-white/10 text-text-muted hover:text-red-400 hover:border-red-400/30 text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed self-start"
              >
                {deletingId === currentShot.shotId ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Trash2 className="w-3 h-3" />
                )}
                {deletingId === currentShot.shotId ? "删除中..." : "删除"}
              </button>
            </div>
          </div>
        </div>

        {/* Shot Thumbnails — B46: red border on failed shots */}
        <div className="flex gap-1.5 overflow-x-auto pb-2 mb-6 scrollbar-hide">
          {shots.map((shot, i) => {
            const isFailed = shot.imageUrl === null;
            return (
              <button
                key={shot.shotId}
                onClick={() => setCurrentIndex(i)}
                title={isFailed ? "图生成失败，点击查看详情" : undefined}
                className={`w-10 h-10 rounded-md flex-shrink-0 border-2 flex items-center justify-center text-[10px] transition-all relative ${
                  i === currentIndex
                    ? isFailed
                      ? "border-red-500 bg-red-500/20 text-red-400"
                      : "border-brand-primary bg-brand-primary/20 text-brand-primary"
                    : isFailed
                    ? "border-red-500/50 bg-red-500/10 text-red-400/70 hover:border-red-500/80"
                    : "border-white/10 bg-bg-secondary text-text-muted hover:border-white/20"
                }`}
              >
                {shot.shotId}
                {isFailed && (
                  <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-red-500 flex items-center justify-center">
                    <span className="text-white text-[7px] font-bold">!</span>
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* BGM Player */}
        <div className="mb-6">
          <BgmPlayer projectId={state.projectId} chapter={1} />
        </div>

        {/* Confirm & Deliver */}
        <button
          onClick={handleDeliver}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 text-base"
        >
          <Sparkles className="w-4 h-4" />
          确认交付
        </button>
        <p className="text-center text-text-muted text-xs mt-3">
          确认后可选择下载漫画包或导出视频
        </p>
      </motion.div>
    </main>
  );
}
