"use client";

import { useState } from "react";
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
} from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";
import BgmPlayer from "./BgmPlayer";
import { useToast } from "@/components/ui/Toast";

export default function StageD() {
  const { state, dispatch } = useCreate();
  const { toast } = useToast();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [editingShotId, setEditingShotId] = useState<number | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [adjustmentText, setAdjustmentText] = useState("");
  const [adjusting, setAdjusting] = useState(false);

  const token = getStoredToken();
  const shots = state.shots;
  const currentShot = shots[currentIndex];

  if (!currentShot) return null;

  const handlePrev = () => setCurrentIndex((i) => Math.max(0, i - 1));
  const handleNext = () => setCurrentIndex((i) => Math.min(shots.length - 1, i + 1));

  // KI-001: Regenerate shot — call POST API then update imageUrl
  const handleRegenerate = async (shotId: number) => {
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
      dispatch({
        type: "REGENERATE_SHOT_SUCCESS",
        payload: { shotId, imageUrl: result.imageUrl },
      });
      toast("success", "重新生成完成");
    } catch {
      toast("error", "重新生成失败，请重试");
    } finally {
      setRegeneratingId(null);
    }
  };

  // Adjust shot image — user provides Chinese intent, backend uses Haiku to modify image_prompt then regenerate
  const handleAdjust = async () => {
    if (!adjustmentText.trim()) return;
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
      dispatch({
        type: "REGENERATE_SHOT_SUCCESS",
        payload: { shotId: currentShot.shotId, imageUrl: result.imageUrl },
      });
      toast("success", "画面已调整");
      setAdjustmentText("");
    } catch {
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

        {/* Shot Navigator */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-text-muted">
            第 {currentIndex + 1} / {shots.length} 张
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
                <div className="w-full h-full flex flex-col items-center justify-center">
                  <ImageIcon className="w-12 h-12 text-text-muted/30 mb-2" />
                  <span className="text-xs text-text-muted">画面生成中...</span>
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

            {/* Narration (read-only) */}
            {currentShot.narrationSegment && (
              <div>
                <label className="text-xs text-text-muted mb-1 block">旁白（只读）</label>
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

            {/* Adjust Image */}
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                <Wand2 className="w-3.5 h-3.5 text-brand-primary" />
                调整画面
              </div>
              <div className="flex gap-2">
                <input
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

        {/* Shot Thumbnails */}
        <div className="flex gap-1.5 overflow-x-auto pb-2 mb-6 scrollbar-hide">
          {shots.map((shot, i) => (
            <button
              key={shot.shotId}
              onClick={() => setCurrentIndex(i)}
              className={`w-10 h-10 rounded-md flex-shrink-0 border-2 flex items-center justify-center text-[10px] transition-all ${
                i === currentIndex
                  ? "border-brand-primary bg-brand-primary/20 text-brand-primary"
                  : "border-white/10 bg-bg-secondary text-text-muted hover:border-white/20"
              }`}
            >
              {shot.shotId}
            </button>
          ))}
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
