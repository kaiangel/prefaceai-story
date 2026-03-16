"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Image from "next/image";

export default function SubPageHeader() {
  return (
    <header className="sticky top-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-b border-bg-tertiary">
      <div className="container-lg flex items-center justify-between h-16">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/brand/logo-40.png" alt="序话Story" width={24} height={24} />
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
