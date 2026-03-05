"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Sparkles,
  Download,
  Play,
  Users,
  Palette,
  Clock,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { getMockStoryDetail } from "@/lib/mock-data";
import { STYLE_PRESETS } from "@/types/create";
import type { StoryDetail } from "@/types/create";

export default function StoryDetailContent() {
  const { storyId } = useParams<{ storyId: string }>();
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [selectedShot, setSelectedShot] = useState(0);

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/login");
      return;
    }
    const detail = getMockStoryDetail(storyId);
    setStory(detail);
  }, [isLoggedIn, storyId, router]);

  if (!isLoggedIn) return null;

  if (!story) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-secondary mb-4">故事不存在</p>
          <Link href="/dashboard" className="text-brand-primary hover:underline text-sm">
            返回工作台
          </Link>
        </div>
      </div>
    );
  }

  const styleLabel = STYLE_PRESETS.find((s) => s.key === story.style)?.label ?? story.style;
  const currentShot = story.shots[selectedShot];

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
        <div className="container-lg flex items-center justify-between h-14">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">返回工作台</span>
          </Link>
          <div className="flex items-center gap-2">
            {story.canContinue && (
              <button className="text-xs py-1.5 px-3 rounded-lg bg-white/5 text-text-secondary hover:bg-white/10 flex items-center gap-1.5 transition-colors">
                <Play className="w-3.5 h-3.5" />
                续写
              </button>
            )}
            <button className="text-xs py-1.5 px-3 rounded-lg bg-brand-primary text-white flex items-center gap-1.5 hover:bg-brand-primary/90 transition-colors">
              <Download className="w-3.5 h-3.5" />
              下载
            </button>
          </div>
        </div>
      </header>

      <main className="container-lg py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Shot Preview */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* Main Image */}
              <div className="relative rounded-xl overflow-hidden bg-bg-secondary border border-white/5 mb-4">
                {currentShot?.imageUrl ? (
                  <img
                    src={currentShot.imageUrl}
                    alt={`Shot ${selectedShot + 1}`}
                    className="w-full max-w-sm mx-auto"
                  />
                ) : (
                  <div className="aspect-[2/3] max-w-sm mx-auto flex items-center justify-center bg-bg-tertiary">
                    <Sparkles className="w-8 h-8 text-text-muted/30" />
                  </div>
                )}

                {/* Navigation arrows */}
                {selectedShot > 0 && (
                  <button
                    onClick={() => setSelectedShot((p) => p - 1)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-bg-primary/80 backdrop-blur-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}
                {selectedShot < story.shots.length - 1 && (
                  <button
                    onClick={() => setSelectedShot((p) => p + 1)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-bg-primary/80 backdrop-blur-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}

                {/* Shot counter */}
                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-bg-primary/80 backdrop-blur-sm text-xs text-text-secondary">
                  {selectedShot + 1} / {story.shots.length}
                </div>
              </div>

              {/* Thumbnails */}
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
                {story.shots.map((shot, i) => (
                  <button
                    key={shot.shotId}
                    onClick={() => setSelectedShot(i)}
                    className={`flex-shrink-0 w-14 h-20 rounded-md overflow-hidden border-2 transition-all ${
                      selectedShot === i
                        ? "border-brand-primary"
                        : "border-transparent opacity-60 hover:opacity-100"
                    }`}
                  >
                    {shot.imageUrl ? (
                      <img src={shot.imageUrl} alt={`Shot ${i + 1}`} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-bg-tertiary" />
                    )}
                  </button>
                ))}
              </div>

              {/* Current shot narration */}
              {currentShot?.narrationSegment && (
                <div className="mt-4 p-3 rounded-lg bg-bg-secondary border border-white/5">
                  <p className="text-xs text-text-muted mb-1">旁白</p>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {currentShot.narrationSegment}
                  </p>
                </div>
              )}
            </motion.div>
          </div>

          {/* Right: Story Info */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="space-y-6"
            >
              {/* Title & Summary */}
              <div>
                <h1 className="text-xl font-bold mb-2">{story.title}</h1>
                <p className="text-sm text-text-tertiary leading-relaxed">{story.summary}</p>
              </div>

              {/* Meta */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Palette className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">{styleLabel}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Sparkles className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">{story.shotCount} 张画面</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">
                    创建于 {new Date(story.createdAt).toLocaleDateString("zh-CN")}
                  </span>
                </div>
              </div>

              {/* Characters */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Users className="w-4 h-4 text-text-muted" />
                  <span className="text-sm text-text-muted">角色</span>
                </div>
                <div className="space-y-2">
                  {story.characters.map((char) => (
                    <div
                      key={char.name}
                      className="p-2.5 rounded-lg bg-bg-secondary border border-white/5"
                    >
                      <p className="text-sm font-medium text-text-primary">{char.name}</p>
                      <p className="text-xs text-text-muted mt-0.5">{char.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Mood */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">情绪基调:</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-primary/10 text-brand-primary">
                  {story.mood}
                </span>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}
