"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, CheckCircle, Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RegisterContent() {
  const { register, isLoggedIn } = useAuth();
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({});
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

  // Redirect if already logged in
  useEffect(() => {
    if (isLoggedIn && !success) {
      router.replace("/dashboard");
    }
  }, [isLoggedIn, success, router]);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (!name.trim()) newErrors.name = "请输入用户名";
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
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const ok = await register({ name: name.trim(), email: email.trim(), password });
    if (ok) {
      setSuccess(true);
      redirectTimerRef.current = setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } else {
      setLoading(false);
      setErrors({ email: "注册失败，请稍后重试" });
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
            <CheckCircle className="w-10 h-10 text-success" />
          </div>
          <h1 className="text-2xl font-bold mb-2">注册成功！</h1>
          <p className="text-text-secondary mb-2">欢迎加入序话Story</p>
          <p className="text-text-tertiary text-sm">正在跳转到工作台...</p>
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
          <h1 className="text-xl font-semibold mb-1">创建账户</h1>
          <p className="text-text-tertiary text-sm">开始你的 AI 创作之旅</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">用户名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (errors.name) setErrors((prev) => ({ ...prev, name: undefined }));
              }}
              placeholder="你的名字"
              className={`w-full px-3.5 py-2.5 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all ${
                errors.name ? "border-error" : "border-white/10"
              }`}
              disabled={loading}
            />
            {errors.name && <p className="text-error text-xs mt-1">{errors.name}</p>}
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
              }}
              placeholder="your@email.com"
              className={`w-full px-3.5 py-2.5 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all ${
                errors.email ? "border-error" : "border-white/10"
              }`}
              disabled={loading}
            />
            {errors.email && <p className="text-error text-xs mt-1">{errors.email}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">密码</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="至少 6 位"
                className={`w-full px-3.5 py-2.5 pr-10 rounded-lg bg-bg-secondary border text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all ${
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
