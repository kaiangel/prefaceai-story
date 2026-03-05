"use client";

import { motion } from "framer-motion";
import { Sparkles, BookOpen } from "lucide-react";
import Link from "next/link";

export default function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <div className="w-20 h-20 rounded-2xl bg-brand-primary/10 flex items-center justify-center mb-6">
        <BookOpen className="w-10 h-10 text-brand-primary/60" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        还没有故事
      </h3>
      <p className="text-text-tertiary text-sm mb-8 max-w-xs">
        输入一个创意，AI 帮你生成完整的条漫故事。每个故事都是独一无二的。
      </p>
      <Link
        href="/create"
        className="btn-primary flex items-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        开始创作
      </Link>
    </motion.div>
  );
}
