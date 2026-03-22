"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { X, Link2, Copy, Check } from "lucide-react";

interface ShareModalProps {
  open: boolean;
  storyTitle: string;
  onClose: () => void;
}

export default function ShareModal({ open, storyTitle, onClose }: ShareModalProps) {
  const [copied, setCopied] = useState(false);
  const mockLink = `https://prefaceai.mov/s/${Date.now().toString(36)}`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(mockLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
            <h3 className="text-lg font-semibold text-text-primary">分享《{storyTitle}》</h3>
            <button onClick={onClose} className="text-text-muted hover:text-text-secondary"><X className="w-5 h-5" /></button>
          </div>

          {/* Link */}
          <div className="flex items-center gap-2 p-3 rounded-lg bg-bg-tertiary border border-white/10 mb-4">
            <Link2 className="w-4 h-4 text-text-muted flex-shrink-0" />
            <span className="text-xs text-text-secondary truncate flex-1">{mockLink}</span>
            <button onClick={handleCopy} className="text-brand-primary hover:underline text-xs flex items-center gap-1 flex-shrink-0 cursor-pointer">
              {copied ? <><Check className="w-3 h-3" />已复制</> : <><Copy className="w-3 h-3" />复制</>}
            </button>
          </div>

          {/* QR Code mock */}
          <div className="flex justify-center mb-4">
            <div className="w-32 h-32 rounded-lg bg-white flex items-center justify-center">
              <div className="w-28 h-28 bg-[repeating-conic-gradient(#000_0%_25%,#fff_0%_50%)] bg-[length:8px_8px] rounded" />
            </div>
          </div>

          {/* Social */}
          <p className="text-xs text-text-muted mb-2 text-center">分享到</p>
          <div className="flex justify-center gap-4">
            {["微信", "微博", "抖音"].map((name) => (
              <button
                key={name}
                className="w-12 h-12 rounded-full bg-bg-tertiary flex items-center justify-center text-text-secondary text-xs hover:bg-white/10 transition-colors cursor-pointer"
              >
                {name}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </>
  );
}
