"use client";

import Link from "next/link";
import { Sparkles, ArrowLeft } from "lucide-react";

export default function SubPageHeader() {
  return (
    <header className="sticky top-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-b border-bg-tertiary">
      <div className="container-lg flex items-center justify-between h-16">
        <Link href="/" className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-brand-primary" />
          <span className="text-lg font-bold text-text-primary">
            序话<span className="text-brand-primary">Story</span>
          </span>
        </Link>
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm text-text-tertiary hover:text-brand-primary transition-colors duration-fast"
        >
          <ArrowLeft className="w-4 h-4" />
          返回首页
        </Link>
      </div>
    </header>
  );
}
