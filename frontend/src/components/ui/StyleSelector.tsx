"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { STYLE_PRESETS, STYLE_PRESETS_DEFAULT_COUNT } from "@/types/create";
import CustomStyleUploader from "./CustomStyleUploader";

interface StyleSelectorProps {
  value: string | null;
  onChange: (value: string | null) => void;
  customStyleImage: File | null;
  customStyleImageUrl: string | null;
  customStyleKeywords: string[];
  onCustomStyleChange: (image: File | null, imageUrl: string | null, keywords: string[], analysis?: Record<string, unknown> | null) => void;
}

export default function StyleSelector({
  value,
  onChange,
  customStyleImage,
  customStyleImageUrl,
  customStyleKeywords,
  onCustomStyleChange,
}: StyleSelectorProps) {
  const [expanded, setExpanded] = useState(false);

  const visiblePresets = expanded
    ? STYLE_PRESETS
    : STYLE_PRESETS.slice(0, STYLE_PRESETS_DEFAULT_COUNT);
  const hasMore = STYLE_PRESETS.length > STYLE_PRESETS_DEFAULT_COUNT;

  const handlePresetClick = (key: string) => {
    onChange(key);
    // 不清空自定义风格 — 自定义风格只能用户手动点 X 删除
    // 自定义风格优先级 > 预设，后端已处理优先级
  };

  const handleCustomUpload = (image: File | null, imageUrl: string | null, keywords: string[], analysis?: Record<string, unknown> | null) => {
    onCustomStyleChange(image, imageUrl, keywords, analysis);
    // 自定义风格上传不清预设（仅作为备选展示），自定义优先
  };

  const hasCustomStyle = !!customStyleImage;

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-text-secondary">视觉风格</label>

      {/* Custom style active hint */}
      {hasCustomStyle && (
        <p className="text-xs text-brand-primary">已使用自定义风格，预设仅供参考</p>
      )}

      {/* Preset Grid */}
      <div className={`grid grid-cols-2 sm:grid-cols-4 gap-3 ${hasCustomStyle ? "opacity-50" : ""}`}>
        <AnimatePresence initial={false}>
          {visiblePresets.map((style) => {
            const isSelected = value === style.key;
            return (
              <motion.button
                key={style.key}
                type="button"
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
                onClick={() => handlePresetClick(style.key)}
                whileTap={{ scale: 0.95 }}
                className={`relative rounded-lg overflow-hidden border transition-colors ${
                  isSelected
                    ? "border-brand-primary shadow-glow-sm"
                    : "border-white/10 hover:border-white/20"
                }`}
              >
                <div
                  className="h-20 sm:h-24 relative"
                  style={{ background: style.gradient }}
                >
                  <img
                    src={style.thumbnail}
                    alt={style.label}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                </div>
                <div className={`px-2 py-1.5 text-center ${
                  isSelected ? "text-brand-primary bg-brand-primary/5" : "text-text-secondary bg-bg-secondary"
                }`}>
                  <div className="text-sm font-medium">{style.label}</div>
                  <div className="text-[10px] text-text-muted">{style.description}</div>
                </div>
                {isSelected && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute top-2 right-2 w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center"
                  >
                    <Check className="w-3 h-3 text-white" />
                  </motion.div>
                )}
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Expand/Collapse toggle */}
      {hasMore && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-center gap-1 w-full py-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          {expanded ? (
            <>收起 <ChevronUp className="w-3.5 h-3.5" /></>
          ) : (
            <>更多风格 <ChevronDown className="w-3.5 h-3.5" /></>
          )}
        </button>
      )}

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 border-t border-white/5" />
        <span className="text-xs text-text-muted">或</span>
        <div className="flex-1 border-t border-white/5" />
      </div>

      {/* Custom Style Upload */}
      <CustomStyleUploader
        image={customStyleImage}
        imageUrl={customStyleImageUrl}
        keywords={customStyleKeywords}
        onUpload={handleCustomUpload}
      />
    </div>
  );
}
