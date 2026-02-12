"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Send, Check, Gift } from "lucide-react";

export default function CTASection() {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || isSubmitting) return;

    setIsSubmitting(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Store in localStorage for demo
    const submissions = JSON.parse(localStorage.getItem("xuhua_submissions") || "[]");
    submissions.push({ email, timestamp: new Date().toISOString() });
    localStorage.setItem("xuhua_submissions", JSON.stringify(submissions));

    setIsSubmitted(true);
    setIsSubmitting(false);
  };

  return (
    <section id="cta" className="section-padding bg-bg-secondary relative overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-primary/10 via-transparent to-accent-purple/5" />

      <div className="container-md relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          {/* Gift Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-primary/10 rounded-full text-brand-primary mb-6">
            <Gift className="w-4 h-4" />
            <span className="text-sm font-medium">限时内测邀请</span>
          </div>

          {/* Title */}
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            开始创作你的故事
          </h2>

          {/* Subtitle */}
          <p className="text-text-secondary mb-2">
            申请内测资格，成为第一批体验者
          </p>
          <p className="text-brand-primary text-sm mb-8">
            注册即送 2 个完整故事创作额度
          </p>

          {/* Form */}
          {!isSubmitted ? (
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              onSubmit={handleSubmit}
              className="max-w-md mx-auto"
            >
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="输入邮箱地址..."
                  required
                  className="flex-1 px-4 py-3 bg-bg-tertiary border border-transparent rounded-lg text-text-primary placeholder:text-text-muted focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20 transition-all duration-fast"
                />
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary animate-glow-pulse disabled:opacity-50 disabled:cursor-not-allowed disabled:animate-none flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      提交中
                    </>
                  ) : (
                    <>
                      申请内测
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </motion.form>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="max-w-md mx-auto bg-success/10 border border-success/30 rounded-lg p-6"
            >
              <div className="w-12 h-12 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-6 h-6 text-success" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">
                申请已提交
              </h3>
              <p className="text-text-secondary">
                我们会在 24 小时内审核并发送邀请码到你的邮箱
              </p>
            </motion.div>
          )}

          {/* Social Proof */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="text-text-muted text-sm mt-8"
          >
            已有 <span className="text-text-secondary font-medium">1,022</span> 人申请内测
          </motion.p>

          {/* Login Link */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="text-text-tertiary text-sm mt-4"
          >
            已有邀请码？
            <a href="/login" className="text-brand-primary hover:underline ml-1">
              直接登录
            </a>
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
