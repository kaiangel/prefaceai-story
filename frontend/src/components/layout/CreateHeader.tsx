"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import UserMenu from "@/components/dashboard/UserMenu";

export default function CreateHeader() {
  const { isLoggedIn } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
      <div className="container-lg flex items-center justify-between h-14">
        <Link href="/" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
          <Sparkles className="w-5 h-5 text-brand-primary" />
          <span className="text-sm font-semibold">序话Story</span>
        </Link>
        <div className="flex items-center gap-3">
          {isLoggedIn ? (
            <>
              <Link
                href="/dashboard"
                className="text-xs text-text-muted hover:text-text-secondary transition-colors"
              >
                工作台
              </Link>
              <UserMenu />
            </>
          ) : (
            <Link
              href="/login"
              className="text-xs text-text-muted hover:text-text-secondary transition-colors"
            >
              登录
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
