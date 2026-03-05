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
  onCustomStyleChange: (image: File | null, imageUrl: string | null, keywords: string[]) => void;
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
    if (customStyleImage) {
      onCustomStyleChange(null, null, []);
    }
  };

  const handleCustomUpload = (image: File | null, imageUrl: string | null, keywords: string[]) => {
    onCustomStyleChange(image, imageUrl, keywords);
    if (image) {
      onChange(null);
    }
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-text-secondary">视觉风格</label>

      {/* Preset Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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
                  className="h-20 sm:h-24"
                  style={{ background: style.gradient }}
                />
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
