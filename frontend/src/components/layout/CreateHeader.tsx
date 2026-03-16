"use client";

import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import UserMenu from "@/components/dashboard/UserMenu";

export default function CreateHeader() {
  const { isLoggedIn } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
      <div className="container-lg flex items-center justify-between h-14">
        <Link href="/" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
          <Image src="/brand/logo-40.png" alt="序话Story" width={24} height={24} />
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
