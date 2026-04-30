"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download,
  Play,
  Pause,
  Users,
  Palette,
  Clock,
  ChevronLeft,
  ChevronRight,
  Heart,
  Share2,
  Copy,
  Trash2,
  Film,
  ImageIcon,
  Music,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken, fetchBgmInfo } from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";
import { STYLE_PRESETS } from "@/types/create";
import type { StoryDetail, Shot } from "@/types/create";
import ShareModal from "@/components/ui/ShareModal";
import ExportModal from "@/components/ui/ExportModal";
import VideoSynthesisModal from "@/components/ui/VideoSynthesisModal";
import ConfirmModal from "@/components/ui/ConfirmModal";

// ─── API response shapes ───────────────────────────────────────────────────────

interface ProjectDetailResponse {
  id: string;
  title: string;
  original_idea: string;
  style_preset: string;
  aspect_ratio: string | null;
  created_at: string;
  confirmed_outline: {
    summary?: string;
    mood?: string;
    user_selected_mood?: string | null;
    music_hint?: string;
    plot_points?: unknown[];
    title?: string;
  } | null;
}

interface ChapterStoryResponse {
  summary: string;
  characters: { name: string; description: string; portrait_url?: string | null }[];
  scenes: {
    scene_id: number;
    narration?: string;
    visual_description?: string;
  }[];
}

interface StoryboardResponse {
  storyboard: unknown;
  chapter_number: number;
  project_id: string;
}

// ─── Fallback: build shots from screenplay scenes (old projects) ───────────────

function buildShotsFromScenes(scenes: ChapterStoryResponse["scenes"]): Shot[] {
  return scenes.map((scene, index) => ({
    shotId: index + 1,
    sceneId: scene.scene_id || index + 1,
    imagePrompt: scene.visual_description || "",
    narrationSegment: scene.narration || "",
    shotType: "auto",
    cameraAngle: "eye level",
    textType: "narration",
    chineseText: [],
    imageUrl: null,
    charactersInScene: [],
  }));
}

// ─── Build shots from storyboard JSON ─────────────────────────────────────────

function buildShotsFromStoryboard(storyboardData: unknown): Shot[] {
  if (!storyboardData) return [];
  const sb = storyboardData as Record<string, unknown>;
  // storyboard_json can be a list of shots OR a dict with a "shots" key
  const rawShots: unknown[] = Array.isArray(sb)
    ? (sb as unknown[])
    : Array.isArray(sb["shots"])
    ? (sb["shots"] as unknown[])
    : [];

  return rawShots.map((shot, index) => {
    const s = shot as Record<string, unknown>;
    const rawImageUrl = (s["image_url"] as string | null | undefined) || null;
    return {
      shotId: (s["shot_id"] as number) || index + 1,
      sceneId: (s["scene_id"] as number) || (s["original_scene_id"] as number) || index + 1,
      imagePrompt: (s["image_prompt"] as string) || "",
      narrationSegment: (s["narration_segment"] as string) || "",
      shotType: (s["shot_type"] as string) || "medium shot",
      cameraAngle: (s["camera_angle"] as string) || "eye level",
      textType: "narration",
      chineseText: [],
      imageUrl: toAbsoluteUrl(rawImageUrl),
      charactersInScene: (s["characters_in_scene"] as string[]) || [],
    };
  });
}

// ─── Inline BGM player ────────────────────────────────────────────────────────

function InlineBgmPlayer({ bgmUrl }: { bgmUrl: string }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-bg-secondary border border-white/5">
      <Music className="w-4 h-4 text-brand-primary flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-text-muted mb-1.5">故事配乐</p>
        <audio
          src={bgmUrl}
          controls
          className="w-full h-8"
          style={{ colorScheme: "dark" }}
        />
      </div>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export default function StoryDetailContent() {
  const { storyId } = useParams<{ storyId: string }>();
  const { isLoggedIn, deleteStory, loadingUser } = useAuth();
  const router = useRouter();

  // Bug A: distinguish loading vs notFound vs loaded
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [bgmUrl, setBgmUrl] = useState<string | null>(null);

  const [selectedShot, setSelectedShot] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(3);
  const [showShare, setShowShare] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const playTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPlayTimer = useCallback(() => {
    if (playTimerRef.current) { clearInterval(playTimerRef.current); playTimerRef.current = null; }
  }, []);

  useEffect(() => {
    if (loadingUser) return;
    if (!isLoggedIn) { router.replace("/login"); return; }

    const token = getStoredToken();
    if (!token) { router.replace("/login"); return; }

    const load = async () => {
      try {
        // Bug B+C: parallel fetch 3 endpoints
        const [project, storyboardData, storyData] = await Promise.all([
          apiFetch<ProjectDetailResponse>(`/projects/${storyId}`, {}, token),
          apiFetch<StoryboardResponse>(
            `/projects/${storyId}/chapters/1/storyboard`,
            {},
            token
          ).catch(() => null),
          apiFetch<ChapterStoryResponse>(
            `/projects/${storyId}/chapters/1/story`,
            {},
            token
          ).catch(() => null),
        ]);

        // Bug G: also fetch BGM info (best-effort, non-blocking)
        fetchBgmInfo(storyId, 1, token)
          .then((info) => {
            if (info.bgm_exists && info.bgm_url) {
              setBgmUrl(toAbsoluteUrl(info.bgm_url));
            }
          })
          .catch(() => null);

        // Bug B+C: prefer storyboard shots (with image_url), fallback to screenplay scenes
        const shots: Shot[] =
          storyboardData?.storyboard
            ? buildShotsFromStoryboard(storyboardData.storyboard)
            : buildShotsFromScenes(storyData?.scenes ?? []);

        // Bug D: use confirmed_outline.summary, fallback to original_idea
        const summary =
          project.confirmed_outline?.summary || project.original_idea || "";

        // Bug E: user_selected_mood > LLM mood > placeholder
        const mood =
          project.confirmed_outline?.user_selected_mood ||
          project.confirmed_outline?.mood ||
          "—";

        // Bug F: characters with portrait_url field
        const characters = (storyData?.characters ?? []).map((c) => ({
          name: c.name,
          description: c.description || "",
          portrait_url: c.portrait_url || null,
        }));

        setStory({
          id: project.id,
          title: project.title || "未命名故事",
          coverImageUrl: "/brand/logo-48.png",
          style: project.style_preset,
          length: "short",
          shotCount: shots.length,
          createdAt: project.created_at,
          updatedAt: project.created_at,
          status: "draft",
          canContinue: true,
          summary,
          characters,
          shots,
          mood,
          aspectRatio: "2:3",
        });
        setLoading(false);
      } catch {
        setLoading(false);
        setNotFound(true);
      }
    };

    void load();
  }, [isLoggedIn, loadingUser, storyId, router]);

  // Auto-play
  useEffect(() => {
    if (!isPlaying || !story) { clearPlayTimer(); return; }
    playTimerRef.current = setInterval(() => {
      setSelectedShot((prev) => {
        if (prev >= story.shots.length - 1) { setIsPlaying(false); return prev; }
        return prev + 1;
      });
    }, playSpeed * 1000);
    return () => clearPlayTimer();
  }, [isPlaying, playSpeed, story, clearPlayTimer]);

  if (loadingUser) return null;
  if (!isLoggedIn) return null;

  // Bug A: show loading skeleton before fetch completes
  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-text-muted text-sm">加载中...</p>
        </div>
      </div>
    );
  }

  if (notFound || !story) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-secondary mb-4">故事不存在</p>
          <Link href="/dashboard" className="text-brand-primary hover:underline text-sm">返回工作台</Link>
        </div>
      </div>
    );
  }

  const styleLabel = STYLE_PRESETS.find((s) => s.key === story.style)?.label ?? story.style;
  const currentShot = story.shots[selectedShot];

  const handleMakeSimilar = () => {
    router.push(`/create?style=${story.style}&length=${story.length}`);
  };

  const handleDelete = async () => {
    await deleteStory(story.id);
    router.push("/dashboard");
  };

  // R7-2: Favorite — POST /projects/{storyId}/favorite, returns { is_favorite }
  const handleFavoriteToggle = async () => {
    const token = getStoredToken();
    if (!token) return;
    // Optimistic update first
    setIsFavorite((prev) => !prev);
    try {
      const r = await apiFetch<{ is_favorite: boolean }>(
        `/projects/${storyId}/favorite`,
        { method: "POST" },
        token
      );
      setIsFavorite(r.is_favorite);
    } catch {
      // Revert optimistic update on failure
      setIsFavorite((prev) => !prev);
    }
  };

  const togglePlay = () => {
    if (isPlaying) { setIsPlaying(false); }
    else { if (selectedShot >= story.shots.length - 1) setSelectedShot(0); setIsPlaying(true); }
  };

  // Bug F: extended characters type for local use
  const characters = story.characters as { name: string; description: string; portrait_url?: string | null }[];

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-lg border-b border-white/5">
        <div className="container-lg flex items-center justify-between h-14">
          <Link href="/dashboard" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">返回</span>
          </Link>
          <div className="flex items-center gap-2">
            <button onClick={handleFavoriteToggle} className={`p-2 rounded-lg transition-colors ${isFavorite ? "text-error" : "text-text-muted hover:text-text-secondary"}`} title="收藏">
              <Heart className={`w-4 h-4 ${isFavorite ? "fill-current" : ""}`} />
            </button>
            <button onClick={() => setShowShare(true)} className="p-2 rounded-lg text-text-muted hover:text-text-secondary transition-colors" title="分享">
              <Share2 className="w-4 h-4" />
            </button>
            <button onClick={handleMakeSimilar} className="text-xs py-1.5 px-3 rounded-lg bg-white/5 text-text-secondary hover:bg-white/10 flex items-center gap-1.5 transition-colors">
              <Copy className="w-3.5 h-3.5" />做同款
            </button>
            <button onClick={() => setShowExport(true)} className="text-xs py-1.5 px-3 rounded-lg bg-white/5 text-text-secondary hover:bg-white/10 flex items-center gap-1.5 transition-colors">
              <Download className="w-3.5 h-3.5" />导出
            </button>
            <button onClick={() => setShowVideo(true)} className="text-xs py-1.5 px-3 rounded-lg bg-brand-primary text-white flex items-center gap-1.5 hover:bg-brand-primary/90 transition-colors">
              <Film className="w-3.5 h-3.5" />合成视频
            </button>
          </div>
        </div>
      </header>

      <main className="container-lg py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Shot Preview */}
          <div className="lg:col-span-2">
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
              {/* Main Image */}
              <div className="relative rounded-xl overflow-hidden bg-bg-secondary border border-white/5 mb-4">
                {currentShot?.imageUrl ? (
                  <img src={currentShot.imageUrl} alt={`Shot ${selectedShot + 1}`} className="w-full max-w-sm mx-auto" />
                ) : (
                  <div className="aspect-[2/3] max-w-sm mx-auto flex items-center justify-center bg-bg-tertiary">
                    <ImageIcon className="w-8 h-8 text-text-muted/30" />
                  </div>
                )}

                {selectedShot > 0 && (
                  <button onClick={() => { setSelectedShot((p) => p - 1); setIsPlaying(false); }} className="absolute left-2 top-1/2 -translate-y-1/2 p-2.5 sm:p-2 rounded-full bg-bg-primary/80 backdrop-blur-sm text-text-secondary hover:text-text-primary transition-colors">
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}
                {selectedShot < story.shots.length - 1 && (
                  <button onClick={() => { setSelectedShot((p) => p + 1); setIsPlaying(false); }} className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 sm:p-2 rounded-full bg-bg-primary/80 backdrop-blur-sm text-text-secondary hover:text-text-primary transition-colors">
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}

                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-bg-primary/80 backdrop-blur-sm text-xs text-text-secondary">
                  {selectedShot + 1} / {story.shots.length}
                </div>
              </div>

              {/* Playback Controls */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <button onClick={togglePlay} className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-primary text-white text-sm font-medium hover:bg-brand-primary/90 transition-colors cursor-pointer">
                  {isPlaying ? <><Pause className="w-4 h-4" />暂停</> : <><Play className="w-4 h-4" />播放</>}
                </button>
                <div className="flex items-center gap-1">
                  {[2, 3, 5].map((s) => (
                    <button key={s} onClick={() => setPlaySpeed(s)} className={`text-xs px-2 py-1 rounded-md transition-colors cursor-pointer ${playSpeed === s ? "bg-brand-primary/20 text-brand-primary" : "bg-white/5 text-text-muted"}`}>
                      {s}s
                    </button>
                  ))}
                </div>
              </div>

              {/* Thumbnails */}
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
                {story.shots.map((shot, i) => (
                  <button key={shot.shotId} onClick={() => { setSelectedShot(i); setIsPlaying(false); }}
                    className={`flex-shrink-0 w-12 h-16 sm:w-14 sm:h-20 rounded-md overflow-hidden border-2 transition-all ${selectedShot === i ? "border-brand-primary" : "border-transparent opacity-60 hover:opacity-100"}`}
                  >
                    {shot.imageUrl ? <img src={shot.imageUrl} alt={`Shot ${i + 1}`} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-bg-tertiary" />}
                  </button>
                ))}
              </div>

              {/* Narration */}
              {currentShot?.narrationSegment && (
                <div className="mt-4 p-3 rounded-lg bg-bg-secondary border border-white/5">
                  <p className="text-xs text-text-muted mb-1">旁白</p>
                  <p className="text-sm text-text-secondary leading-relaxed">{currentShot.narrationSegment}</p>
                </div>
              )}
            </motion.div>
          </div>

          {/* Right: Story Info */}
          <div>
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="space-y-6">
              <div>
                <h1 className="text-lg sm:text-xl font-bold mb-2">{story.title}</h1>
                <p className="text-sm text-text-tertiary leading-relaxed">{story.summary}</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Palette className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">{styleLabel}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <ImageIcon className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">{story.shotCount} 张画面</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4 text-text-muted" />
                  <span className="text-text-secondary">创建于 {new Date(story.createdAt).toLocaleDateString("zh-CN")}</span>
                </div>
              </div>

              {/* Bug F: Characters with portrait + silhouette fallback */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Users className="w-4 h-4 text-text-muted" />
                  <span className="text-sm text-text-muted">角色</span>
                </div>
                <div className="space-y-2">
                  {characters.map((char) => (
                    <div key={char.name} className="flex items-center gap-2.5 p-2.5 rounded-lg bg-bg-secondary border border-white/5">
                      {/* Portrait or silhouette */}
                      <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden bg-bg-tertiary flex items-center justify-center">
                        {char.portrait_url ? (
                          <img
                            src={toAbsoluteUrl(char.portrait_url) ?? ""}
                            alt={char.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-text-muted/40">
                            <circle cx="12" cy="7" r="4" />
                            <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" />
                          </svg>
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text-primary">{char.name}</p>
                        <p className="text-xs text-text-muted mt-0.5 truncate">{char.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bug E: mood from confirmed_outline */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">情绪基调:</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-primary/10 text-brand-primary">{story.mood}</span>
              </div>

              {/* Bug G: BGM player */}
              {bgmUrl && <InlineBgmPlayer bgmUrl={bgmUrl} />}

              {/* Delete */}
              <button onClick={() => setShowDeleteConfirm(true)} className="flex items-center gap-1.5 text-xs text-error hover:underline cursor-pointer">
                <Trash2 className="w-3.5 h-3.5" />删除故事
              </button>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Modals */}
      <ShareModal open={showShare} storyTitle={story.title} storyId={storyId} onClose={() => setShowShare(false)} />
      <ExportModal open={showExport} onClose={() => setShowExport(false)} onExport={() => {}} />
      <VideoSynthesisModal open={showVideo} onClose={() => setShowVideo(false)} />
      <ConfirmModal
        open={showDeleteConfirm}
        title="删除故事"
        message={`确定删除《${story.title}》？此操作不可撤销。`}
        confirmLabel="删除"
        danger
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
