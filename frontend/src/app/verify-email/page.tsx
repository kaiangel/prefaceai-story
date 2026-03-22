"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { CheckCircle } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function VerifyEmailPage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearTimer();
          router.push("/create");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearTimer();
  }, [router, clearTimer]);

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center max-w-sm"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <Image src="/brand/logo-48.png" alt="序话Story" width={32} height={32} />
          <span className="text-2xl font-bold text-text-primary">
            序话<span className="text-brand-primary">Story</span>
          </span>
        </div>

        {/* Success Icon */}
        <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-10 h-10 text-success" />
        </div>

        <h1 className="text-2xl font-bold text-text-primary mb-3">邮箱验证成功！</h1>
        <p className="text-text-secondary mb-6">
          你的账户已激活，即将进入创作工作台...
        </p>

        {/* Countdown */}
        <div className="flex items-center justify-center gap-2 text-text-tertiary text-sm">
          <div className="w-8 h-8 rounded-full border-2 border-brand-primary flex items-center justify-center text-brand-primary font-bold text-sm">
            {countdown}
          </div>
          <span>秒后自动跳转</span>
        </div>

        {/* Manual link */}
        <button
          onClick={() => router.push("/create")}
          className="mt-6 text-brand-primary hover:underline text-sm cursor-pointer"
        >
          立即进入
        </button>
      </motion.div>
    </div>
  );
}
