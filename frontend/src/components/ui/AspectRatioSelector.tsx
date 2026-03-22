"use client";

import { motion } from "framer-motion";
import { Smartphone, Monitor, Square, Image } from "lucide-react";
import type { AspectRatio } from "@/types/create";

interface AspectRatioSelectorProps {
  value: AspectRatio;
  onChange: (value: AspectRatio) => void;
}

const options: { key: AspectRatio; label: string; description: string; Icon: typeof Monitor; badge?: string }[] = [
  { key: "2:3", label: "竖屏 2:3", description: "抖音竖屏", Icon: Smartphone, badge: "默认" },
  { key: "3:4", label: "竖屏 3:4", description: "小红书图文", Icon: Image },
  { key: "1:1", label: "方形 1:1", description: "朋友圈", Icon: Square },
  { key: "16:9", label: "横屏 16:9", description: "B站 / YouTube", Icon: Monitor },
];

export default function AspectRatioSelector({ value, onChange }: AspectRatioSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">画面比例</label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {options.map((opt) => {
          const selected = value === opt.key;
          return (
            <motion.button
              key={opt.key}
              onClick={() => onChange(opt.key)}
              whileTap={{ scale: 0.97 }}
              className={`relative flex flex-col items-center gap-2 p-3 rounded-lg border transition-colors text-center ${
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
              {opt.badge && (
                <span className="absolute top-1.5 right-1.5 text-[9px] px-1.5 py-0.5 rounded-full bg-brand-primary/15 text-brand-primary font-medium">
                  {opt.badge}
                </span>
              )}
              <opt.Icon className={`w-5 h-5 ${selected ? "text-brand-primary" : "text-text-muted"}`} />
              <div>
                <div className={`text-sm font-medium ${selected ? "text-text-primary" : "text-text-secondary"}`}>
                  {opt.label}
                </div>
                <div className="text-[11px] text-text-muted">{opt.description}</div>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
