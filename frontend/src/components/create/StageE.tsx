"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Download,
  Video,
  Images,
  Check,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";

export default function StageE() {
  const { state, dispatch } = useCreate();
  const [downloading, setDownloading] = useState<"comic" | "video" | null>(null);
  const [downloaded, setDownloaded] = useState<Set<string>>(new Set());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleDownload = (format: "comic" | "video") => {
    setDownloading(format);
    // Mock download
    timerRef.current = setTimeout(() => {
      setDownloading(null);
      setDownloaded((prev) => new Set(prev).add(format));
      timerRef.current = null;
    }, 2000);
  };

  const handleNewStory = () => {
    dispatch({ type: "RESET" });
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-lg mx-auto text-center"
      >
        {/* Success Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", bounce: 0.5 }}
          className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6"
        >
          <Check className="w-8 h-8 text-green-500" />
        </motion.div>

        <h1 className="text-2xl font-bold mb-2">故事创作完成</h1>
        {/* P1-6 (UX-17): Show outline.summary (edited outline) instead of original_idea.
            Three-layer fallback: outline.summary → chapter.summary → original idea */}
        {(state.outline?.summary || state.idea) && (
          <p className="text-text-secondary text-sm mb-3 max-w-sm mx-auto line-clamp-3 leading-relaxed">
            {state.outline?.summary || state.idea}
          </p>
        )}
        <p className="text-text-tertiary text-sm mb-2">
          共 {state.shots.length} 张画面
          {state.bgm && <> &middot; BGM: {state.bgm.name}</>}
        </p>
        <p className="text-text-muted text-xs mb-8">
          选择你想要的交付方式
        </p>

        {/* Download Cards */}
        <div className="space-y-4 mb-8">
          {/* Comic Package */}
          <motion.button
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onClick={() => handleDownload("comic")}
            disabled={downloading !== null}
            className={`w-full text-left p-5 rounded-xl border transition-all ${
              downloaded.has("comic")
                ? "border-green-500/30 bg-green-500/5"
                : "border-white/5 bg-bg-secondary hover:border-white/10"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-brand-primary/10 flex items-center justify-center flex-shrink-0">
                <Images className="w-6 h-6 text-brand-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary">漫画打包下载</p>
                <p className="text-xs text-text-muted mt-0.5">
                  参考图 + 带文字 Shot 图 + BGM，可二次创作
                </p>
              </div>
              {downloading === "comic" ? (
                <Loader2 className="w-5 h-5 text-brand-primary animate-spin flex-shrink-0" />
              ) : downloaded.has("comic") ? (
                <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
              ) : (
                <Download className="w-5 h-5 text-text-muted flex-shrink-0" />
              )}
            </div>
          </motion.button>

          {/* Video Download */}
          <motion.button
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            onClick={() => handleDownload("video")}
            disabled={downloading !== null}
            className={`w-full text-left p-5 rounded-xl border transition-all ${
              downloaded.has("video")
                ? "border-green-500/30 bg-green-500/5"
                : "border-white/5 bg-bg-secondary hover:border-white/10"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                <Video className="w-6 h-6 text-purple-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary">视频下载</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Shot 序列 + BGM 合成视频，可直接发布
                </p>
              </div>
              {downloading === "video" ? (
                <Loader2 className="w-5 h-5 text-purple-400 animate-spin flex-shrink-0" />
              ) : downloaded.has("video") ? (
                <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
              ) : (
                <Download className="w-5 h-5 text-text-muted flex-shrink-0" />
              )}
            </div>
          </motion.button>
        </div>

        {/* New Story */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          onClick={handleNewStory}
          className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
        >
          开始新故事
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </motion.div>
    </main>
  );
}
