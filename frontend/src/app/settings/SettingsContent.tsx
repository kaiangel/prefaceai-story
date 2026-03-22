"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Camera, ArrowLeft, Crown, Coins, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function SettingsContent() {
  const { user, isLoggedIn, updateUser } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [nickname, setNickname] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/login");
    }
  }, [isLoggedIn, router]);

  useEffect(() => {
    if (user) {
      setNickname(user.name);
      setAvatarPreview(user.avatarUrl);
    }
  }, [user]);

  if (!isLoggedIn || !user) return null;

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setAvatarPreview(url);
    }
  };

  const handleSave = () => {
    updateUser({ name: nickname.trim() || user.name, avatarUrl: avatarPreview });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // Mock data
  const membershipData = {
    level: "Pro",
    expiresAt: "2026-12-31",
    credits: 87,
    history: [
      { id: "1", title: "雨夜公交站", credits: 5, date: "2026-03-20" },
      { id: "2", title: "深夜便利店", credits: 3, date: "2026-03-18" },
      { id: "3", title: "外卖小哥的奇遇", credits: 5, date: "2026-03-15" },
    ],
  };

  const initials = user.name
    .split(/[\s_-]/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
        <div className="container-lg flex items-center h-14 gap-3">
          <button onClick={() => router.back()} className="text-text-secondary hover:text-text-primary transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-sm font-semibold text-text-primary">个人设置</h1>
        </div>
      </header>

      <main className="container-lg py-8 max-w-lg mx-auto space-y-6">
        {/* Avatar + Nickname */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-bg-secondary rounded-xl border border-white/5 p-6"
        >
          <h2 className="text-sm font-medium text-text-secondary mb-4">个人资料</h2>

          {/* Avatar */}
          <div className="flex items-center gap-4 mb-5">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="relative w-16 h-16 rounded-full overflow-hidden bg-bg-tertiary group cursor-pointer flex-shrink-0"
            >
              {avatarPreview ? (
                <img src={avatarPreview} alt="头像" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-lg font-bold text-brand-primary">
                  {initials}
                </div>
              )}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera className="w-5 h-5 text-white" />
              </div>
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
            <div className="flex-1">
              <p className="text-xs text-text-muted mb-1">昵称</p>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-bg-tertiary border border-white/10 text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all"
              />
            </div>
          </div>

          {/* Email (read-only) */}
          <div className="mb-4">
            <p className="text-xs text-text-muted mb-1">邮箱</p>
            <p className="px-3 py-2 rounded-lg bg-bg-tertiary/50 text-text-tertiary text-sm">
              {user.email}
            </p>
          </div>

          <button
            onClick={handleSave}
            className="btn-primary text-sm py-2 px-5"
          >
            {saved ? "已保存" : "保存"}
          </button>
        </motion.section>

        {/* Membership */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-bg-secondary rounded-xl border border-white/5 p-6"
        >
          <h2 className="text-sm font-medium text-text-secondary mb-4">会员状态</h2>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-brand-primary" />
              <span className="text-lg font-bold text-text-primary">{membershipData.level}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-primary/15 text-brand-primary font-medium">
                有效期至 {membershipData.expiresAt}
              </span>
            </div>
          </div>
          <div className="flex gap-3">
            <button className="flex-1 py-2 rounded-lg border border-brand-primary/30 text-brand-primary text-sm hover:bg-brand-primary/10 transition-colors cursor-pointer">
              升级到 Max
            </button>
            <button className="flex-1 py-2 rounded-lg border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors cursor-pointer">
              续期
            </button>
          </div>
        </motion.section>

        {/* Credits */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-bg-secondary rounded-xl border border-white/5 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-text-secondary">Credits 余额</h2>
            <div className="flex items-center gap-1.5">
              <Coins className="w-4 h-4 text-accent-gold" />
              <span className="text-lg font-bold text-text-primary">{membershipData.credits}</span>
            </div>
          </div>

          {/* History */}
          <p className="text-xs text-text-muted mb-2">消耗历史</p>
          <div className="space-y-2">
            {membershipData.history.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div>
                  <p className="text-sm text-text-primary">{item.title}</p>
                  <p className="text-xs text-text-muted">{item.date}</p>
                </div>
                <span className="text-sm text-error font-medium">-{item.credits}</span>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Quick Links */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-bg-secondary rounded-xl border border-white/5 divide-y divide-white/5"
        >
          <Link href="/dashboard" className="flex items-center justify-between px-6 py-4 hover:bg-white/5 transition-colors">
            <span className="text-sm text-text-primary">我的工作台</span>
            <ChevronRight className="w-4 h-4 text-text-muted" />
          </Link>
          <Link href="/create" className="flex items-center justify-between px-6 py-4 hover:bg-white/5 transition-colors">
            <span className="text-sm text-text-primary">创建新故事</span>
            <ChevronRight className="w-4 h-4 text-text-muted" />
          </Link>
        </motion.section>
      </main>
    </div>
  );
}
