"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, Layers, Clock, CheckCircle, Coins, Loader2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import UserMenu from "@/components/dashboard/UserMenu";
import StoryGrid from "@/components/dashboard/StoryGrid";

export default function DashboardContent() {
  const { user, isLoggedIn, stories, deleteStory, loadingUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loadingUser && !isLoggedIn) {
      router.replace("/login");
    }
  }, [isLoggedIn, loadingUser, router]);

  if (loadingUser) return null;
  if (!isLoggedIn || !user) return null;

  const completedCount = stories.filter((s) => s.status === "complete").length;
  const totalShots = stories.reduce((sum, s) => sum + s.shotCount, 0);
  const generatingStory = stories.find((s) => s.status === "generating");

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleContinue = (_storyId: string) => {
    router.push("/create");
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
        <div className="container-lg flex items-center justify-between h-14">
          <Link href="/" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors group">
            <Image src="/brand/logo-40.png" alt="序话Story" width={22} height={22} className="transition-transform duration-fast group-hover:scale-110" />
            <span className="text-sm font-semibold">序话Story</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/create"
              className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              新建故事
            </Link>
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="container-lg py-8">
        {/* Generating Banner */}
        {generatingStory && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Link
              href={`/dashboard/${generatingStory.id}`}
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-warning/10 border border-warning/20 hover:bg-warning/15 transition-colors"
            >
              <Loader2 className="w-4 h-4 text-warning animate-spin flex-shrink-0" />
              <span className="text-sm text-text-primary flex-1">
                《{generatingStory.title}》正在生成中... <span className="text-warning font-medium">67%</span>
              </span>
              <span className="text-xs text-text-muted">点击查看</span>
            </Link>
          </motion.div>
        )}

        {/* Welcome */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold mb-1">
            {getGreeting()}，{user.name}
          </h1>
          <p className="text-text-tertiary text-sm">管理你的故事创作</p>
        </motion.div>

        {/* Stats Cards */}
        {stories.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-8"
          >
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-4 h-4 text-brand-primary" />
                <span className="text-xs text-text-muted">故事总数</span>
              </div>
              <p className="text-2xl font-bold text-text-primary">{stories.length}</p>
            </div>
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-success" />
                <span className="text-xs text-text-muted">已完成</span>
              </div>
              <p className="text-2xl font-bold text-text-primary">{completedCount}</p>
            </div>
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-warning" />
                <span className="text-xs text-text-muted">总画面数</span>
              </div>
              <p className="text-2xl font-bold text-text-primary">{totalShots}</p>
            </div>
            <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Coins className="w-4 h-4 text-accent-gold" />
                <span className="text-xs text-text-muted">Credits</span>
              </div>
              <p className="text-2xl font-bold text-text-primary">{user.credits ?? 0}</p>
            </div>
          </motion.div>
        )}

        {/* Story Grid */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <StoryGrid
            stories={stories}
            onDelete={deleteStory}
            onContinue={handleContinue}
          />
        </motion.div>
      </main>
    </div>
  );
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了";
  if (hour < 12) return "早上好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
}
