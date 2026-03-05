"use client";

import { motion } from "framer-motion";
import { Monitor, Smartphone } from "lucide-react";
import type { AspectRatio } from "@/types/create";

interface AspectRatioSelectorProps {
  value: AspectRatio;
  onChange: (value: AspectRatio) => void;
}

const options: { key: AspectRatio; label: string; description: string; Icon: typeof Monitor }[] = [
  { key: "2:3", label: "竖屏 2:3", description: "抖音 / 小红书", Icon: Smartphone },
  { key: "16:9", label: "横屏 16:9", description: "B站 / YouTube", Icon: Monitor },
];

export default function AspectRatioSelector({ value, onChange }: AspectRatioSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">画面比例</label>
      <div className="grid grid-cols-2 gap-3">
        {options.map((opt) => {
          const selected = value === opt.key;
          return (
            <motion.button
              key={opt.key}
              onClick={() => onChange(opt.key)}
              whileTap={{ scale: 0.97 }}
              className={`relative flex items-center gap-3 p-3 rounded-lg border transition-colors text-left ${
                selected
                  ? "border-brand-primary bg-brand-primary/10"
                  : "border-white/10 bg-bg-secondary hover:border-white/20"
              }`}
            >
              {selected && (
                <motion.div
                  layoutId="aspect-indicator"
                  className="absolute inset-0 rounded-lg border-2 border-brand-primary"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <opt.Icon className={`w-5 h-5 ${selected ? "text-brand-primary" : "text-text-muted"}`} />
              <div>
                <div className={`text-sm font-medium ${selected ? "text-text-primary" : "text-text-secondary"}`}>
                  {opt.label}
                </div>
                <div className="text-xs text-text-muted">{opt.description}</div>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
