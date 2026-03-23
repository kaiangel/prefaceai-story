"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock, Ticket } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RegisterContent() {
  const { register, isLoggedIn, loadingUser } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agreedTerms, setAgreedTerms] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; inviteCode?: string; terms?: string }>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    if (redirectTimerRef.current) {
      clearTimeout(redirectTimerRef.current);
      redirectTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  useEffect(() => {
    if (!loadingUser && isLoggedIn && !success) {
      router.replace("/dashboard");
    }
  }, [isLoggedIn, loadingUser, success, router]);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (!email.trim()) {
      newErrors.email = "请输入邮箱";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "邮箱格式不正确";
    }
    if (!password) {
      newErrors.password = "请输入密码";
    } else if (password.length < 6) {
      newErrors.password = "密码至少 6 位";
    }
    if (!inviteCode.trim()) {
      newErrors.inviteCode = "请输入邀请码";
    }
    if (!agreedTerms) {
      newErrors.terms = "请阅读并同意服务条款";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const ok = await register({ email: email.trim(), password, inviteCode: inviteCode.trim() });
    if (ok) {
      setSuccess(true);
    } else {
      setLoading(false);
      setErrors({ inviteCode: "邀请码无效，请检查后重试" });
    }
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
            <Mail className="w-10 h-10 text-success" />
          </div>
          <h1 className="text-2xl font-bold mb-2">验证邮件已发送</h1>
          <p className="text-text-secondary mb-2">
            请查收 <span className="text-brand-primary">{email}</span> 的验证邮件
          </p>
          <p className="text-text-tertiary text-sm mb-4">点击邮件中的链接完成注册</p>
          {/* Dev mode: simulate email verification */}
          <Link
            href="/verify-email"
            className="text-xs text-text-muted hover:text-brand-primary transition-colors"
          >
            （开发模式）模拟验证 →
          </Link>
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
            <Image src="/brand/logo-48.png" alt="序话Story" width={32} height={32} />
            <span className="text-2xl font-bold">序话Story</span>
          </div>
          <h1 className="text-xl font-semibold mb-1">创建账户</h1>
          <p className="text-text-tertiary text-sm">使用邀请码注册，开始 AI 创作之旅</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">邮箱</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
                }}
                placeholder="your@email.com"
                className={`w-full pl-10 pr-3.5 py-2.5 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all ${
                  errors.email ? "border-error" : "border-white/10"
                }`}
                disabled={loading}
              />
            </div>
            {errors.email && <p className="text-error text-xs mt-1">{errors.email}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">密码</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="至少 6 位"
                className={`w-full pl-10 pr-10 py-2.5 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all ${
                  errors.password ? "border-error" : "border-white/10"
                }`}
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && <p className="text-error text-xs mt-1">{errors.password}</p>}
          </div>

          {/* Invite Code */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">邀请码</label>
            <div className="relative">
              <Ticket className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
              <input
                type="text"
                value={inviteCode}
                onChange={(e) => {
                  setInviteCode(e.target.value.toUpperCase());
                  if (errors.inviteCode) setErrors((prev) => ({ ...prev, inviteCode: undefined }));
                }}
                placeholder="输入你收到的邀请码"
                className={`w-full pl-10 pr-3.5 py-2.5 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all uppercase tracking-wider ${
                  errors.inviteCode ? "border-error" : "border-white/10"
                }`}
                disabled={loading}
              />
            </div>
            {errors.inviteCode && <p className="text-error text-xs mt-1">{errors.inviteCode}</p>}
          </div>

          {/* Terms */}
          <div>
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={agreedTerms}
                onChange={(e) => {
                  setAgreedTerms(e.target.checked);
                  if (errors.terms) setErrors((prev) => ({ ...prev, terms: undefined }));
                }}
                className="mt-0.5 w-4 h-4 rounded border-white/20 bg-bg-tertiary text-brand-primary focus:ring-brand-primary/50 cursor-pointer"
                disabled={loading}
              />
              <span className="text-xs text-text-tertiary leading-relaxed">
                我已阅读并同意{" "}
                <Link href="/terms" className="text-brand-primary hover:underline">服务条款</Link>
                {" "}和{" "}
                <Link href="/privacy" className="text-brand-primary hover:underline">隐私政策</Link>
              </span>
            </label>
            {errors.terms && <p className="text-error text-xs mt-1">{errors.terms}</p>}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                注册中...
              </>
            ) : (
              "注册"
            )}
          </button>
        </form>

        {/* Bottom links */}
        <div className="mt-8 text-center space-y-3">
          <p className="text-text-tertiary text-sm">
            已有账户？{" "}
            <Link href="/login" className="text-brand-primary hover:underline">
              登录
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
