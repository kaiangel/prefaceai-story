"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, Eye, EyeOff, Mail, Lock } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginContent() {
  const { login, isLoggedIn } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSent, setForgotSent] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);

  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const forgotTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    if (redirectTimerRef.current) {
      clearTimeout(redirectTimerRef.current);
      redirectTimerRef.current = null;
    }
    if (forgotTimerRef.current) {
      clearTimeout(forgotTimerRef.current);
      forgotTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  useEffect(() => {
    if (isLoggedIn && !success) {
      router.replace("/dashboard");
    }
  }, [isLoggedIn, success, router]);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (!email.trim()) {
      newErrors.email = "请输入邮箱";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "邮箱格式不正确";
    }
    if (!password) {
      newErrors.password = "请输入密码";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const ok = await login(email.trim(), password);
    if (ok) {
      setSuccess(true);
      redirectTimerRef.current = setTimeout(() => {
        router.push("/dashboard");
      }, 1200);
    } else {
      setLoading(false);
      setErrors({ password: "邮箱或密码错误" });
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(forgotEmail)) return;
    setForgotLoading(true);
    await new Promise((r) => { forgotTimerRef.current = setTimeout(r, 1000); });
    setForgotLoading(false);
    setForgotSent(true);
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
          <p className="text-text-secondary mb-2">欢迎回到序话Story</p>
          <p className="text-text-tertiary text-sm">即将进入工作台...</p>
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
          <h1 className="text-xl font-semibold mb-1">欢迎回来</h1>
          <p className="text-text-tertiary text-sm">登录你的账户继续创作</p>
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
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm text-text-secondary">密码</label>
              <button
                type="button"
                onClick={() => { setShowForgot(true); setForgotEmail(email); setForgotSent(false); }}
                className="text-xs text-brand-primary hover:underline"
              >
                忘记密码?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="输入密码"
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

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                登录中...
              </>
            ) : (
              "登录"
            )}
          </button>
        </form>

        {/* Bottom links */}
        <div className="mt-8 text-center space-y-3">
          <p className="text-text-tertiary text-sm">
            没有账户？{" "}
            <Link href="/register" className="text-brand-primary hover:underline">
              注册
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

      {/* Forgot Password Modal */}
      <AnimatePresence>
        {showForgot && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-50"
              onClick={() => setShowForgot(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="fixed inset-0 z-50 flex items-center justify-center px-4"
            >
              <div className="bg-bg-secondary border border-white/10 rounded-xl p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
                {forgotSent ? (
                  <div className="text-center py-2">
                    <div className="w-14 h-14 rounded-full bg-success/15 flex items-center justify-center mx-auto mb-4">
                      <Mail className="w-7 h-7 text-success" />
                    </div>
                    <h3 className="text-lg font-semibold text-text-primary mb-2">重置链接已发送</h3>
                    <p className="text-text-tertiary text-sm mb-4">
                      请查收 <span className="text-brand-primary">{forgotEmail}</span> 的邮件
                    </p>
                    <button onClick={() => setShowForgot(false)} className="text-sm text-brand-primary hover:underline">
                      返回登录
                    </button>
                  </div>
                ) : (
                  <>
                    <h3 className="text-lg font-semibold text-text-primary mb-2">忘记密码</h3>
                    <p className="text-text-tertiary text-sm mb-4">输入注册邮箱，我们将发送密码重置链接</p>
                    <form onSubmit={handleForgotSubmit}>
                      <input
                        type="email"
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="w-full px-3.5 py-2.5 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all mb-3"
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setShowForgot(false)}
                          className="flex-1 py-2.5 rounded-lg border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors"
                        >
                          取消
                        </button>
                        <button
                          type="submit"
                          disabled={forgotLoading || !forgotEmail.trim()}
                          className="flex-1 btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {forgotLoading ? "发送中..." : "发送重置链接"}
                        </button>
                      </div>
                    </form>
                  </>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
