"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { X, Film, CheckCircle, Download } from "lucide-react";

interface VideoSynthesisModalProps {
  open: boolean;
  onClose: () => void;
}

export default function VideoSynthesisModal({ open, onClose }: VideoSynthesisModalProps) {
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  useEffect(() => {
    if (!open) { setProgress(0); setDone(false); clearTimer(); return; }
    timerRef.current = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) { clearTimer(); setDone(true); return 100; }
        return prev + Math.random() * 15 + 5;
      });
    }, 400);
    return () => clearTimer();
  }, [open, clearTimer]);

  if (!open) return null;

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 bg-black/60 z-50" onClick={done ? onClose : undefined} />
      <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-bg-secondary border border-white/10 rounded-xl p-6 w-full max-w-sm text-center"
          onClick={(e) => e.stopPropagation()}
        >
          {done ? (
            <>
              <div className="w-14 h-14 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-7 h-7 text-success" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">视频已生成</h3>
              <p className="text-text-tertiary text-sm mb-4">MP4 格式，可直接发布到抖音等平台</p>
              <div className="flex gap-3">
                <button onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-white/10 text-text-secondary text-sm cursor-pointer">关闭</button>
                <button onClick={onClose} className="flex-1 py-2.5 rounded-lg bg-brand-primary text-white text-sm font-medium flex items-center justify-center gap-1.5 cursor-pointer">
                  <Download className="w-4 h-4" />下载视频
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="w-14 h-14 rounded-full bg-brand-primary/10 flex items-center justify-center mx-auto mb-4">
                <Film className="w-7 h-7 text-brand-primary animate-pulse" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">正在合成视频</h3>
              <p className="text-text-tertiary text-sm mb-4">合成中，请稍候...</p>
              <div className="w-full h-2 bg-bg-tertiary rounded-full overflow-hidden mb-2">
                <motion.div
                  className="h-full bg-brand-primary rounded-full"
                  animate={{ width: `${Math.min(progress, 100)}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-xs text-text-muted">{Math.min(Math.round(progress), 100)}%</p>
              <button onClick={onClose} className="mt-4 text-xs text-text-muted hover:text-text-secondary cursor-pointer">
                <X className="w-3.5 h-3.5 inline mr-1" />取消
              </button>
            </>
          )}
        </motion.div>
      </div>
    </>
  );
}
