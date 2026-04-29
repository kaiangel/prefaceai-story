"use client";

import { motion } from "framer-motion";
import { Clock, Layers, Play, Trash2, MoreHorizontal } from "lucide-react";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";
import type { StoryCard as StoryCardType } from "@/types/create";
import { STYLE_PRESETS } from "@/types/create";

interface StoryCardProps {
  story: StoryCardType;
  index: number;
  onDelete?: (id: string) => void;
  onContinue?: (id: string) => void;
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  draft: { label: "草稿", color: "text-text-muted" },
  generating: { label: "生成中", color: "text-warning" },
  complete: { label: "已完成", color: "text-success" },
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const hours = d.getHours().toString().padStart(2, "0");
  const mins = d.getMinutes().toString().padStart(2, "0");
  return `${month}/${day} ${hours}:${mins}`;
}

export default function StoryCard({ story, index, onDelete, onContinue }: StoryCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const styleLabel = STYLE_PRESETS.find((s) => s.key === story.style)?.label ?? story.style;
  const status = STATUS_LABELS[story.status] ?? STATUS_LABELS.complete;

  const closeMenu = useCallback(() => setShowMenu(false), []);

  useEffect(() => {
    if (!showMenu) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMenu();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showMenu, closeMenu]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className="group relative bg-bg-secondary rounded-xl border border-white/5 overflow-hidden hover:border-white/10 transition-all"
    >
      {/* Cover Image */}
      <Link href={`/dashboard/${story.id}`}>
        <div className="relative aspect-[3/4] bg-bg-tertiary overflow-hidden">
          {story.coverImageUrl ? (
            <img
              src={story.coverImageUrl}
              alt={story.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Layers className="w-10 h-10 text-text-muted/30" />
            </div>
          )}
          {/* Status badge */}
          <div className="absolute top-2 left-2">
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full bg-bg-primary/80 backdrop-blur-sm ${status.color}`}>
              {status.label}
            </span>
          </div>
          {/* Shot count badge */}
          <div className="absolute bottom-2 right-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-bg-primary/80 backdrop-blur-sm text-text-secondary">
              {story.shotCount} shots
            </span>
          </div>
          {/* Generating progress overlay */}
          {story.status === "generating" && (
            <div className="absolute inset-x-0 bottom-0">
              <div className="bg-bg-primary/80 backdrop-blur-sm px-2 py-1.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-warning">生成中...</span>
                  <span className="text-[10px] text-text-muted">67%</span>
                </div>
                <div className="w-full h-1 bg-bg-tertiary rounded-full overflow-hidden">
                  <div className="h-full bg-warning rounded-full animate-pulse" style={{ width: "67%" }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </Link>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <Link href={`/dashboard/${story.id}`} className="flex-1 min-w-0">
            <h3 className="font-medium text-sm text-text-primary truncate group-hover:text-brand-primary transition-colors">
              {story.title}
            </h3>
          </Link>
          {/* Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              aria-label="故事操作菜单"
              className="p-1 rounded-md text-text-muted hover:text-text-secondary hover:bg-white/5 transition-colors"
            >
              <MoreHorizontal className="w-3.5 h-3.5" />
            </button>
            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <div className="absolute right-0 top-full mt-1 z-20 bg-bg-tertiary border border-white/10 rounded-lg shadow-lg py-1 min-w-[120px]">
                  {story.canContinue && onContinue && (
                    <button
                      onClick={() => { onContinue(story.id); setShowMenu(false); }}
                      className="w-full text-left px-3 py-1.5 text-sm text-text-secondary hover:bg-white/5 flex items-center gap-2"
                    >
                      <Play className="w-3.5 h-3.5" />
                      续写
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => { onDelete(story.id); setShowMenu(false); }}
                      className="w-full text-left px-3 py-1.5 text-sm text-error hover:bg-white/5 flex items-center gap-2"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      删除
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 mt-1.5 text-[11px] text-text-muted">
          <span className="px-1.5 py-0.5 rounded bg-white/5">{styleLabel}</span>
          {story.mood && (
            <span className="px-1.5 py-0.5 rounded bg-white/5">{story.mood}</span>
          )}
          <span className="flex items-center gap-0.5 ml-auto">
            <Clock className="w-3 h-3" />
            {formatDate(story.updatedAt)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
