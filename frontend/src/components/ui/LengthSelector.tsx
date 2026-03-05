"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Zap, BookOpen, Layers, Library } from "lucide-react";
import type { StoryLength, ContinuationMode } from "@/types/create";
import { LENGTH_OPTIONS } from "@/types/create";

const ICON_MAP: Record<string, typeof Zap> = {
  Zap,
  BookOpen,
  Layers,
  Library,
};

interface LengthSelectorProps {
  value: StoryLength;
  onChange: (value: StoryLength) => void;
  continuationMode: ContinuationMode | null;
  onContinuationModeChange: (mode: ContinuationMode | null) => void;
}

export default function LengthSelector({
  value,
  onChange,
  continuationMode,
  onContinuationModeChange,
}: LengthSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">故事篇幅</label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {LENGTH_OPTIONS.map((option) => {
          const isSelected = value === option.key;
          const Icon = ICON_MAP[option.icon] || BookOpen;
          return (
            <motion.button
              key={option.key}
              type="button"
              onClick={() => onChange(option.key)}
              whileTap={{ scale: 0.97 }}
              className={`relative p-3 sm:p-4 rounded-lg border text-left transition-colors ${
                isSelected
                  ? "border-brand-primary bg-brand-primary/5 shadow-glow-sm"
                  : "border-white/10 bg-bg-secondary hover:border-white/20"
              }`}
            >
              {isSelected && (
                <motion.div
                  layoutId="length-indicator"
                  className="absolute inset-0 rounded-lg border-2 border-brand-primary pointer-events-none"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <div className="flex items-start gap-2">
                <div className={`mt-0.5 ${isSelected ? "text-brand-primary" : "text-text-muted"}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`font-semibold text-sm ${isSelected ? "text-text-primary" : "text-text-secondary"}`}>
                      {option.label}
                    </span>
                    {option.key === "short" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-brand-primary/15 text-brand-primary font-medium">
                        推荐
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted mt-0.5">{option.description}</p>
                  <p className="text-xs text-text-tertiary mt-1">{option.shotCount}</p>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Epic continuation mode sub-options */}
      <AnimatePresence>
        {value === "epic" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pt-2 space-y-2">
              <label className="text-xs font-medium text-text-muted">续写模式</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => onContinuationModeChange("auto")}
                  className={`px-3 py-2 rounded-lg border text-left text-sm transition-colors ${
                    continuationMode === "auto"
                      ? "border-brand-primary bg-brand-primary/10 text-text-primary"
                      : "border-white/10 bg-bg-secondary text-text-muted hover:border-white/20"
                  }`}
                >
                  <div className="font-medium">自动续写</div>
                  <div className="text-[10px] text-text-muted mt-0.5">AI 自动推进剧情</div>
                </button>
                <button
                  type="button"
                  onClick={() => onContinuationModeChange("user-directed")}
                  className={`px-3 py-2 rounded-lg border text-left text-sm transition-colors ${
                    continuationMode === "user-directed"
                      ? "border-brand-primary bg-brand-primary/10 text-text-primary"
                      : "border-white/10 bg-bg-secondary text-text-muted hover:border-white/20"
                  }`}
                >
                  <div className="font-medium">手动引导</div>
                  <div className="text-[10px] text-text-muted mt-0.5">每章结束后你来定方向</div>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
