"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, SlidersHorizontal } from "lucide-react";
import type { StoryCard as StoryCardType } from "@/types/create";
import StoryCard from "./StoryCard";
import EmptyState from "./EmptyState";

interface StoryGridProps {
  stories: StoryCardType[];
  onDelete?: (id: string) => void;
  onContinue?: (id: string) => void;
  newlyCompletedIds?: Set<string>;
}

type SortBy = "updatedAt" | "createdAt" | "title";
type FilterStatus = "all" | "complete" | "generating" | "draft";

export default function StoryGrid({ stories, onDelete, onContinue, newlyCompletedIds }: StoryGridProps) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("updatedAt");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [showFilters, setShowFilters] = useState(false);

  // Filter
  let filtered = stories;
  if (search.trim()) {
    const q = search.trim().toLowerCase();
    filtered = filtered.filter(
      (s) => s.title.toLowerCase().includes(q) || s.style.toLowerCase().includes(q)
    );
  }
  if (filterStatus !== "all") {
    filtered = filtered.filter((s) => s.status === filterStatus);
  }

  // Sort
  filtered = [...filtered].sort((a, b) => {
    if (sortBy === "title") return a.title.localeCompare(b.title, "zh");
    return new Date(b[sortBy]).getTime() - new Date(a[sortBy]).getTime();
  });

  if (stories.length === 0) {
    return <EmptyState />;
  }

  return (
    <div>
      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索故事..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-bg-secondary border border-white/10 text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`p-2 rounded-lg border transition-colors ${
            showFilters ? "bg-brand-primary/10 border-brand-primary/30 text-brand-primary" : "bg-bg-secondary border-white/10 text-text-muted hover:text-text-secondary"
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>
      </div>

      {/* Filter Options */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="flex flex-wrap items-center gap-3 mb-6"
        >
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">状态:</span>
            {(["all", "complete", "generating", "draft"] as FilterStatus[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilterStatus(f)}
                className={`text-xs px-2 py-1 rounded-md transition-colors ${
                  filterStatus === f
                    ? "bg-brand-primary/20 text-brand-primary"
                    : "bg-white/5 text-text-muted hover:text-text-secondary"
                }`}
              >
                {{ all: "全部", complete: "已完成", generating: "生成中", draft: "草稿" }[f]}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">排序:</span>
            {([
              ["updatedAt", "最近更新"],
              ["createdAt", "创建时间"],
              ["title", "标题"],
            ] as [SortBy, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setSortBy(key)}
                className={`text-xs px-2 py-1 rounded-md transition-colors ${
                  sortBy === key
                    ? "bg-brand-primary/20 text-brand-primary"
                    : "bg-white/5 text-text-muted hover:text-text-secondary"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Results count */}
      {search.trim() && (
        <p className="text-xs text-text-muted mb-4">
          找到 {filtered.length} 个故事
        </p>
      )}

      {/* Grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((story, i) => (
            <StoryCard
              key={story.id}
              story={story}
              index={i}
              onDelete={onDelete}
              onContinue={onContinue}
              isNewlyCompleted={newlyCompletedIds?.has(story.id) ?? false}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-text-muted text-sm">没有找到匹配的故事</p>
        </div>
      )}
    </div>
  );
}
