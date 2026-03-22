"use client";

import { motion } from "framer-motion";
import { X, ImageIcon, Music, Package } from "lucide-react";

interface ExportModalProps {
  open: boolean;
  onClose: () => void;
  onExport: (format: "images" | "images_audio" | "all") => void;
}

const OPTIONS = [
  { key: "images" as const, icon: ImageIcon, label: "仅图片", desc: "所有 Shot 图片（PNG）" },
  { key: "images_audio" as const, icon: Music, label: "图片 + 音频", desc: "Shot 图片 + 旁白音频" },
  { key: "all" as const, icon: Package, label: "全部素材", desc: "图片 + 音频 + 角色参考图 + 场景图" },
];

export default function ExportModal({ open, onClose, onExport }: ExportModalProps) {
  if (!open) return null;

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 bg-black/60 z-50" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-bg-secondary border border-white/10 rounded-xl p-6 w-full max-w-sm"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary">导出素材</h3>
            <button onClick={onClose} className="text-text-muted hover:text-text-secondary"><X className="w-5 h-5" /></button>
          </div>

          <div className="space-y-2">
            {OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => { onExport(opt.key); onClose(); }}
                className="w-full flex items-center gap-3 p-3 rounded-lg bg-bg-tertiary border border-white/5 hover:border-brand-primary/30 hover:bg-brand-primary/5 transition-all cursor-pointer text-left"
              >
                <opt.icon className="w-5 h-5 text-brand-primary flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-text-primary">{opt.label}</p>
                  <p className="text-xs text-text-muted">{opt.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </>
  );
}
