"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import {
  Music,
  Play,
  Pause,
  RefreshCw,
  Shuffle,
  Volume2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import {
  fetchBgmInfo,
  regenerateBgm,
  changeMetaBgm,
  patchBgmVolume,
  getStoredToken,
} from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";

// Debounce utility for volume PATCH (300ms)
function useDebouncedCallback<T extends (...args: Parameters<T>) => void>(
  fn: T,
  delay: number
): T {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  return useCallback(
    ((...args: Parameters<T>) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => fn(...args), delay);
    }) as T,
    [fn, delay] // eslint-disable-line react-hooks/exhaustive-deps
  );
}

function metaVersionLabel(v: string | null): string {
  if (v === "mixed") return "混合版";
  if (v === "en") return "英文版";
  return "未知版本";
}

interface BgmPlayerProps {
  projectId: string | null;
  chapter?: number;
}

export default function BgmPlayer({ projectId, chapter = 1 }: BgmPlayerProps) {
  const { state, dispatch } = useCreate();
  const { bgmPlayer } = state;
  const token = getStoredToken();

  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);

  // ── On mount: fetch BGM info from backend ──────────────────────────────────
  useEffect(() => {
    if (!projectId || !token) {
      // [BgmPlayer] Log #1 — skip fetch: no projectId or token
      // eslint-disable-next-line no-console
      console.log("[BgmPlayer] useEffect: skip fetch (no projectId or token)", { projectId, hasToken: !!token });
      return;
    }
    if (bgmPlayer.status !== "idle") {
      // [BgmPlayer] Log #2 — skip fetch: already fetched
      // eslint-disable-next-line no-console
      console.log("[BgmPlayer] useEffect: skip fetch (status already:", bgmPlayer.status, "bgmUrl:", bgmPlayer.bgmUrl?.slice(0, 60) ?? "null", ")");
      return;
    }

    // [BgmPlayer] Log #3 — starting BGM info fetch
    // eslint-disable-next-line no-console
    console.log("[BgmPlayer] useEffect: fetching BGM info for projectId=", projectId, "chapter=", chapter);
    dispatch({ type: "BGM_LOADING" });
    fetchBgmInfo(projectId, chapter, token)
      .then((info) => {
        // [BgmPlayer] Log #4 — BGM info response
        // eslint-disable-next-line no-console
        console.log("[BgmPlayer] fetchBgmInfo response: bgm_exists=", info.bgm_exists, "bgm_url=", info.bgm_url?.slice(0, 80) ?? "null", "meta_version=", info.meta_version, "credits_used=", info.credits_used);
        if (!info.bgm_exists || !info.bgm_url) {
          // [BgmPlayer] Log #5 — no BGM available
          // eslint-disable-next-line no-console
          console.log("[BgmPlayer] BGM not available (bgm_exists=false or bgm_url null) → BGM_NO_BGM");
          dispatch({ type: "BGM_NO_BGM" });
        } else {
          // [BgmPlayer] Log #6 — BGM ready
          // eslint-disable-next-line no-console
          console.log("[BgmPlayer] BGM ready → BGM_READY url=", info.bgm_url?.slice(0, 80));
          dispatch({
            type: "BGM_READY",
            payload: {
              bgmUrl: info.bgm_url,
              volume: info.bgm_volume,
              metaVersion: info.meta_version,
              creditsUsed: info.credits_used,
            },
          });
        }
      })
      .catch((e) => {
        // [BgmPlayer] Log #7 — fetch error → treat as no BGM
        // eslint-disable-next-line no-console
        console.warn("[BgmPlayer] fetchBgmInfo ERROR (→ BGM_NO_BGM):", e instanceof Error ? e.message : e);
        dispatch({ type: "BGM_NO_BGM" });
      });
  }, [projectId, chapter, token]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Sync volume on HTML audio element ──────────────────────────────────────
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = bgmPlayer.volume / 100;
    }
  }, [bgmPlayer.volume]);

  // ── Reload audio when bgmUrl changes ───────────────────────────────────────
  useEffect(() => {
    if (audioRef.current && bgmPlayer.bgmUrl) {
      audioRef.current.load();
      setIsPlaying(false);
      setAudioCurrentTime(0);
      setAudioDuration(null);
    }
  }, [bgmPlayer.bgmUrl]);

  // ── Volume PATCH with 300ms debounce ───────────────────────────────────────
  const patchVolumeFn = useCallback(
    (vol: number) => {
      if (!projectId || !token) return;
      patchBgmVolume(projectId, chapter, vol / 100, token).catch(() => {
        // silent fail — volume saved locally even if API fails
      });
    },
    [projectId, chapter, token]
  );

  const debouncedPatchVolume = useDebouncedCallback(patchVolumeFn, 300);

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = Number(e.target.value);
    dispatch({ type: "BGM_SET_VOLUME", payload: vol });
    debouncedPatchVolume(vol);
  };

  // ── Play / Pause ────────────────────────────────────────────────────────────
  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    }
  };

  // ── Regenerate BGM ──────────────────────────────────────────────────────────
  const handleRegenerate = async () => {
    if (!projectId || !token) return;
    // [BgmPlayer] Log #8 — regenerate BGM start (用户点"再来一首")
    // eslint-disable-next-line no-console
    console.log("[BgmPlayer] handleRegenerate: regenerating BGM for projectId=", projectId, "chapter=", chapter);
    dispatch({ type: "BGM_GENERATING" });
    setIsPlaying(false);
    try {
      const res = await regenerateBgm(projectId, chapter, token);
      // [BgmPlayer] Log #9 — regenerate success
      // eslint-disable-next-line no-console
      console.log("[BgmPlayer] handleRegenerate: SUCCESS new_bgm_url=", res.bgm_url?.slice(0, 80) ?? "null", "meta_version=", res.meta_version, "credits=", res.total_credits_used);
      dispatch({
        type: "BGM_READY",
        payload: {
          bgmUrl: res.bgm_url,
          volume: bgmPlayer.volume / 100,
          metaVersion: res.meta_version as "mixed" | "en" | null,
          creditsUsed: res.total_credits_used,
        },
      });
    } catch (e) {
      // [BgmPlayer] Log #10 — regenerate error
      // eslint-disable-next-line no-console
      console.error("[BgmPlayer] handleRegenerate: ERROR:", e instanceof Error ? e.message : e);
      dispatch({ type: "BGM_ERROR", payload: "重新生成失败，请稍后重试" });
    }
  };

  // ── Change Meta (换一首) ─────────────────────────────────────────────────────
  const handleChangeMeta = async () => {
    if (!projectId || !token) return;
    // [BgmPlayer] Log #11 — change meta start (用户点"换种风格")
    // eslint-disable-next-line no-console
    console.log("[BgmPlayer] handleChangeMeta: changing BGM style for projectId=", projectId, "chapter=", chapter);
    dispatch({ type: "BGM_GENERATING" });
    setIsPlaying(false);
    try {
      const res = await changeMetaBgm(projectId, chapter, token);
      // [BgmPlayer] Log #12 — change meta success
      // eslint-disable-next-line no-console
      console.log("[BgmPlayer] handleChangeMeta: SUCCESS new_bgm_url=", res.bgm_url?.slice(0, 80) ?? "null", "meta_version=", res.meta_version, "credits=", res.total_credits_used);
      dispatch({
        type: "BGM_READY",
        payload: {
          bgmUrl: res.bgm_url,
          volume: bgmPlayer.volume / 100,
          metaVersion: res.meta_version as "mixed" | "en" | null,
          creditsUsed: res.total_credits_used,
        },
      });
    } catch (e) {
      // [BgmPlayer] Log #13 — change meta error
      // eslint-disable-next-line no-console
      console.error("[BgmPlayer] handleChangeMeta: ERROR:", e instanceof Error ? e.message : e);
      dispatch({ type: "BGM_ERROR", payload: "换一首失败，请稍后重试" });
    }
  };

  // ── First-time generate (when bgm_exists=false) ─────────────────────────────
  const handleFirstGenerate = async () => {
    if (!projectId || !token) return;
    dispatch({ type: "BGM_GENERATING" });
    try {
      const res = await regenerateBgm(projectId, chapter, token);
      dispatch({
        type: "BGM_READY",
        payload: {
          bgmUrl: res.bgm_url,
          volume: bgmPlayer.volume / 100,
          metaVersion: res.meta_version as "mixed" | "en" | null,
          creditsUsed: res.total_credits_used,
        },
      });
    } catch {
      dispatch({ type: "BGM_ERROR", payload: "生成配乐失败，请稍后重试" });
    }
  };

  // ── Time formatting helper ──────────────────────────────────────────────────
  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  // ── mock credits display (pure frontend per spec) ───────────────────────────
  const creditsDisplay = bgmPlayer.creditsUsed;

  // ══════════════════════════════════════════════════════════════════════════
  // Render states
  // ══════════════════════════════════════════════════════════════════════════

  // Loading (initial fetch)
  if (bgmPlayer.status === "loading") {
    return (
      <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
        <div className="flex items-center gap-2 text-sm text-text-secondary mb-3">
          <Music className="w-4 h-4 text-brand-primary" />
          <span className="font-medium">配乐</span>
        </div>
        <div className="flex items-center gap-2 text-text-muted text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>正在加载配乐...</span>
        </div>
      </div>
    );
  }

  // Generating (AI making music, 90-300s)
  if (bgmPlayer.status === "generating") {
    return (
      <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <Music className="w-4 h-4 text-brand-primary" />
            <span className="font-medium">配乐</span>
          </div>
          <span className="text-[11px] text-text-muted">已消耗 {creditsDisplay} credits</span>
        </div>
        <div className="flex flex-col items-center gap-3 py-4">
          {/* Animated progress bar */}
          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-brand-primary/60 rounded-full animate-pulse w-2/3" />
          </div>
          <div className="flex items-center gap-2 text-text-muted text-sm">
            <Loader2 className="w-4 h-4 animate-spin text-brand-primary" />
            <span>AI 正在生成音乐，约需 2-5 分钟...</span>
          </div>
          <p className="text-[11px] text-text-muted/70">请保持页面打开，生成完成后自动播放</p>
        </div>
      </div>
    );
  }

  // No BGM (bgm_exists=false, or initial idle without projectId)
  if (bgmPlayer.status === "idle" || (bgmPlayer.status === "error" && !bgmPlayer.bgmUrl)) {
    return (
      <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <Music className="w-4 h-4 text-brand-primary" />
            <span className="font-medium">配乐</span>
          </div>
        </div>
        {bgmPlayer.status === "error" && bgmPlayer.errorMessage && (
          <div className="flex items-center gap-2 text-red-400 text-xs mb-3">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{bgmPlayer.errorMessage}</span>
          </div>
        )}
        <div className="text-center py-3">
          <p className="text-sm text-text-muted mb-3">暂无配乐</p>
          {projectId && token && (
            <button
              onClick={handleFirstGenerate}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-primary/10 border border-brand-primary/30 text-brand-primary text-sm font-medium hover:bg-brand-primary/20 transition-colors"
            >
              <Music className="w-3.5 h-3.5" />
              生成配乐
            </button>
          )}
        </div>
      </div>
    );
  }

  // Error with existing BGM url (retry allowed)
  if (bgmPlayer.status === "error") {
    return (
      <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <Music className="w-4 h-4 text-brand-primary" />
            <span className="font-medium">配乐</span>
          </div>
          <span className="text-[11px] text-text-muted">已消耗 {creditsDisplay} credits</span>
        </div>
        <div className="flex items-center gap-2 text-red-400 text-xs mb-3">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{bgmPlayer.errorMessage || "生成失败"}</span>
        </div>
        <button
          onClick={handleRegenerate}
          className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 text-text-muted hover:text-text-secondary hover:border-white/20 text-xs transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          重试
        </button>
      </div>
    );
  }

  // Ready — full player UI
  return (
    <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <Music className="w-4 h-4 text-brand-primary" />
          <span className="font-medium">配乐</span>
        </div>
        <span className="text-[11px] text-brand-primary/80 bg-brand-primary/10 px-2 py-0.5 rounded-full">
          已消耗 {creditsDisplay} credits
        </span>
      </div>

      {/* Hidden HTML5 audio element */}
      {/* P0-1: toAbsoluteUrl converts /static/... paths to absolute backend URLs */}
      {bgmPlayer.bgmUrl && (
        <audio
          ref={audioRef}
          src={toAbsoluteUrl(bgmPlayer.bgmUrl) ?? bgmPlayer.bgmUrl}
          onEnded={() => setIsPlaying(false)}
          onLoadedMetadata={(e) => setAudioDuration((e.target as HTMLAudioElement).duration)}
          onTimeUpdate={(e) => setAudioCurrentTime((e.target as HTMLAudioElement).currentTime)}
          preload="metadata"
        />
      )}

      {/* Play button + progress */}
      <div className="flex items-center gap-3 mb-3">
        <button
          onClick={togglePlay}
          className="w-9 h-9 rounded-full bg-brand-primary/20 border border-brand-primary/30 flex items-center justify-center text-brand-primary hover:bg-brand-primary/30 transition-colors flex-shrink-0"
          aria-label={isPlaying ? "暂停" : "播放"}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
        </button>
        <div className="flex-1">
          {/* Progress bar */}
          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mb-1">
            <div
              className="h-full bg-brand-primary rounded-full transition-all"
              style={{
                width:
                  audioDuration && audioDuration > 0
                    ? `${(audioCurrentTime / audioDuration) * 100}%`
                    : "0%",
              }}
            />
          </div>
          {/* Time display */}
          <div className="flex justify-between text-[10px] text-text-muted">
            <span>{formatTime(audioCurrentTime)}</span>
            <span>{audioDuration ? formatTime(audioDuration) : "--:--"}</span>
          </div>
        </div>
      </div>

      {/* Volume slider */}
      <div className="flex items-center gap-2 mb-3">
        <Volume2 className="w-3.5 h-3.5 text-text-muted flex-shrink-0" />
        <input
          type="range"
          min={0}
          max={100}
          value={bgmPlayer.volume}
          onChange={handleVolumeChange}
          className="flex-1 h-1.5 accent-brand-primary cursor-pointer"
          aria-label="音量"
        />
        <span className="text-[10px] text-text-muted w-7 text-right">{bgmPlayer.volume}%</span>
      </div>

      {/* Meta version */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-text-muted">
          版本：<span className="text-text-secondary">{metaVersionLabel(bgmPlayer.metaVersion)}</span>
        </span>
      </div>

      {/* Action buttons — B24: distinct labels so users instantly understand the difference */}
      <div className="flex gap-2">
        <button
          onClick={handleChangeMeta}
          title="切换 BGM 风格类型（mixed 混合版 ↔ en 英文版），换不同调性和语言风格"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 text-text-muted hover:text-text-secondary hover:border-white/20 text-xs transition-colors"
        >
          <Shuffle className="w-3 h-3" />
          换种风格
        </button>
        <button
          onClick={handleRegenerate}
          title="保持相同风格，用同样的调性和语言再生成一首变奏版本"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 text-text-muted hover:text-text-secondary hover:border-white/20 text-xs transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          再来一首
        </button>
      </div>
      <p className="text-[10px] text-text-muted/60 text-center mt-2">
        <span className="font-medium text-text-muted/80">换种风格</span> 消耗 5 credits（试不同调性）&nbsp;·&nbsp;
        <span className="font-medium text-text-muted/80">再来一首</span> 消耗 10 credits（同款变奏）
      </p>
    </div>
  );
}
