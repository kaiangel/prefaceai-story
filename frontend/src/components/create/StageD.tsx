"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Trash2,
  Music,
  Check,
  X,
  Image as ImageIcon,
  Sparkles,
} from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { BGM_TRACKS } from "@/types/create";

export default function StageD() {
  const { state, dispatch } = useCreate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [editingShotId, setEditingShotId] = useState<number | null>(null);
  const [showBGM, setShowBGM] = useState(false);

  const shots = state.shots;
  const currentShot = shots[currentIndex];

  if (!currentShot) return null;

  const handlePrev = () => setCurrentIndex((i) => Math.max(0, i - 1));
  const handleNext = () => setCurrentIndex((i) => Math.min(shots.length - 1, i + 1));

  const handleRegenerate = (shotId: number) => {
    dispatch({ type: "REGENERATE_SHOT", payload: shotId });
  };

  const handleDelete = (shotId: number) => {
    dispatch({ type: "DELETE_SHOT", payload: shotId });
    if (currentIndex >= shots.length - 1 && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
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
          <div className="flex gap-2">
            <button
              onClick={() => setShowBGM(!showBGM)}
              className={`p-2 rounded-lg border transition-colors ${
                showBGM
                  ? "border-brand-primary/50 bg-brand-primary/10 text-brand-primary"
                  : "border-white/10 text-text-muted hover:text-text-secondary"
              }`}
            >
              <Music className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Shot Card */}
        <div className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden mb-4">
          {/* Image Area */}
          <div className="bg-bg-primary flex items-center justify-center relative">
            <div className="w-full max-w-sm mx-auto aspect-[2/3]">
              {currentShot.imageUrl ? (
                <img
                  src={currentShot.imageUrl}
                  alt={`Shot ${currentShot.shotId}`}
                  className="w-full h-full object-cover"
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
                className="w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white disabled:opacity-30 pointer-events-auto transition-opacity"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNext}
                disabled={currentIndex === shots.length - 1}
                className="w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white disabled:opacity-30 pointer-events-auto transition-opacity"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Shot Info */}
          <div className="p-4 space-y-3">
            {/* Narration */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs text-text-muted">旁白文字</label>
                {editingShotId === currentShot.shotId ? (
                  <button
                    onClick={() => setEditingShotId(null)}
                    className="text-xs text-brand-primary flex items-center gap-1"
                  >
                    <Check className="w-3 h-3" />
                    完成
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
                  value={currentShot.narrationSegment}
                  onChange={(e) =>
                    dispatch({
                      type: "UPDATE_SHOT_TEXT",
                      payload: {
                        shotId: currentShot.shotId,
                        field: "narrationSegment",
                        value: e.target.value,
                      },
                    })
                  }
                  rows={3}
                  className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-2 text-text-primary text-sm resize-none focus:outline-none focus:border-brand-primary/50"
                />
              ) : (
                <p className="text-sm text-text-secondary leading-relaxed">
                  {currentShot.narrationSegment}
                </p>
              )}
            </div>

            {/* Shot Meta */}
            <div className="flex items-center gap-3 text-[10px] text-text-muted">
              <span>镜头: {currentShot.shotType}</span>
              <span>角度: {currentShot.cameraAngle}</span>
              <span>场景: {currentShot.sceneId}</span>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => handleRegenerate(currentShot.shotId)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 text-text-muted hover:text-text-secondary hover:border-white/20 text-xs transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                重新生成
              </button>
              <button
                onClick={() => handleDelete(currentShot.shotId)}
                className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg border border-white/10 text-text-muted hover:text-red-400 hover:border-red-400/30 text-xs transition-colors"
              >
                <Trash2 className="w-3 h-3" />
                删除
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

        {/* BGM Selector */}
        <AnimatePresence>
          {showBGM && (
            <motion.section
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 overflow-hidden"
            >
              <div className="bg-bg-secondary rounded-xl p-4 border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-text-secondary">背景音乐</h3>
                  <button
                    onClick={() => setShowBGM(false)}
                    className="text-text-muted hover:text-text-secondary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-2">
                  {BGM_TRACKS.map((track) => (
                    <button
                      key={track.id}
                      onClick={() => dispatch({ type: "SET_BGM", payload: track })}
                      className={`w-full flex items-center gap-3 p-2.5 rounded-lg border transition-all text-left ${
                        state.bgm?.id === track.id
                          ? "border-brand-primary/50 bg-brand-primary/10"
                          : "border-white/5 hover:border-white/10"
                      }`}
                    >
                      <Music className="w-4 h-4 text-text-muted flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-text-primary truncate">{track.name}</p>
                        <p className="text-[10px] text-text-muted">
                          {track.mood} &middot; {track.duration}
                        </p>
                      </div>
                      {state.bgm?.id === track.id && (
                        <Check className="w-4 h-4 text-brand-primary flex-shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </motion.section>
          )}
        </AnimatePresence>

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
