"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, CheckCircle } from "lucide-react";
import Link from "next/link";
import InviteCodeInput from "@/components/ui/InviteCodeInput";

const DEMO_CODE = "XUHUA2026";

export default function LoginContent() {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [shake, setShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const shakeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const apiTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    if (shakeTimerRef.current) {
      clearTimeout(shakeTimerRef.current);
      shakeTimerRef.current = null;
    }
    if (apiTimerRef.current) {
      clearTimeout(apiTimerRef.current);
      apiTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!code.trim()) {
      setError("请输入邀请码");
      return;
    }
    if (code.trim().length < 4) {
      setError("邀请码格式不正确");
      return;
    }

    setError("");
    setLoading(true);

    // Simulate API call
    await new Promise<void>((resolve) => {
      apiTimerRef.current = setTimeout(resolve, 1000);
    });

    if (code.trim() === DEMO_CODE) {
      setSuccess(true);
    } else {
      setLoading(false);
      setError("邀请码无效，请检查后重试");
      setShake(true);
      if (shakeTimerRef.current) clearTimeout(shakeTimerRef.current);
      shakeTimerRef.current = setTimeout(() => setShake(false), 500);
    }
  };

  const handleCodeChange = (value: string) => {
    setCode(value);
    if (error) setError("");
  };

  if (success) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-success" />
          </div>
          <h1 className="text-2xl font-bold mb-2">登录成功！</h1>
          <p className="text-text-secondary mb-2">欢迎体验序话Story</p>
          <p className="text-text-tertiary text-sm">即将进入创作工作台...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="w-8 h-8 text-brand-primary" />
            <span className="text-2xl font-bold">序话Story</span>
          </div>
          <h1 className="text-xl font-semibold mb-1">欢迎回来</h1>
          <p className="text-text-tertiary text-sm">输入邀请码开始创作</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <motion.div
            animate={shake ? { x: [-10, 10, -10, 10, 0] } : {}}
            transition={{ duration: 0.4 }}
          >
            <InviteCodeInput
              ref={inputRef}
              value={code}
              onChange={handleCodeChange}
              error={error}
              disabled={loading}
            />
          </motion.div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                验证中...
              </>
            ) : (
              "登录"
            )}
          </button>
        </form>

        {/* Bottom links */}
        <div className="mt-8 text-center space-y-3">
          <p className="text-text-tertiary text-sm">
            没有邀请码？{" "}
            <Link
              href="/#cta"
              className="text-brand-primary hover:underline"
            >
              申请内测
            </Link>
          </p>
          <Link
            href="/"
            className="text-text-muted hover:text-text-secondary text-sm transition-colors block"
          >
            返回首页
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
