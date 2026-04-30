/**
 * R7-2: Public share page — /s/[token]
 *
 * No auth required. Fetches story preview via GET /api/share/{token}.
 * Shows cover image + title + first 3 preview shots.
 * CTA: "想看完整故事？立即注册" → /login
 *
 * OG meta tags:暂不加（记 PENDING，Founder 决策）
 */

import { notFound } from "next/navigation";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

interface SharePageData {
  story_title: string;
  cover_image_url: string | null;
  preview_shots: Array<{
    shot_id: number;
    image_url: string | null;
    narration_segment?: string;
    chinese_text?: string;
  }>;
  is_full_access: boolean;
}

async function fetchShareData(token: string): Promise<SharePageData | null> {
  try {
    const res = await fetch(`${API_BASE}/share/${token}`, {
      // No auth header — public endpoint
      next: { revalidate: 60 }, // cache 60s
    });
    if (!res.ok) return null;
    return (await res.json()) as SharePageData;
  } catch {
    return null;
  }
}

function toAbsoluteServerUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const serverBase = API_BASE.replace("/api", "");
  return `${serverBase}${url}`;
}

interface Props {
  params: { token: string };
}

export default async function SharePage({ params }: Props) {
  const data = await fetchShareData(params.token);

  if (!data) {
    notFound();
  }

  const previewShots = (data.preview_shots || []).slice(0, 3);

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <Link href="/" className="text-text-primary font-semibold text-sm">
          序话 Story
        </Link>
        <Link
          href="/login"
          className="text-xs px-3 py-1.5 rounded-lg bg-brand-primary text-white hover:bg-brand-primary/90 transition-colors"
        >
          登录
        </Link>
      </header>

      {/* Content */}
      <main className="flex-1 flex flex-col items-center px-4 py-8 max-w-lg mx-auto w-full">
        {/* Title */}
        <h1 className="text-2xl font-bold text-text-primary text-center mb-2">
          {data.story_title}
        </h1>
        <p className="text-text-tertiary text-sm mb-6 text-center">
          在序话 Story 上创作的故事画册
        </p>

        {/* Preview shots grid */}
        {previewShots.length > 0 ? (
          <div
            className={`w-full grid gap-3 mb-8 ${
              previewShots.length === 1
                ? "grid-cols-1"
                : previewShots.length === 2
                ? "grid-cols-2"
                : "grid-cols-3"
            }`}
          >
            {previewShots.map((shot, idx) => {
              const absUrl = toAbsoluteServerUrl(shot.image_url);
              return (
                <div key={shot.shot_id || idx} className="rounded-xl overflow-hidden border border-white/5 bg-bg-secondary">
                  <div className="aspect-[2/3] relative bg-bg-tertiary">
                    {absUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={absUrl}
                        alt={`画面 ${idx + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-text-muted/30 text-xs">画面 {idx + 1}</span>
                      </div>
                    )}
                  </div>
                  {shot.chinese_text && (
                    <p className="text-xs text-text-secondary px-2 py-1.5 truncate">
                      {shot.chinese_text}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="w-full h-48 rounded-xl border border-white/5 bg-bg-secondary flex items-center justify-center mb-8">
            <p className="text-text-muted text-sm">暂无预览画面</p>
          </div>
        )}

        {/* Blur overlay hinting more content */}
        {!data.is_full_access && previewShots.length >= 3 && (
          <p className="text-text-muted text-xs text-center mb-4">
            还有更多精彩画面...
          </p>
        )}

        {/* CTA */}
        <div className="w-full space-y-3">
          <Link
            href="/login"
            className="w-full flex items-center justify-center py-3 rounded-xl bg-brand-primary text-white font-medium hover:bg-brand-primary/90 transition-colors"
          >
            想看完整故事？立即注册
          </Link>
          <p className="text-center text-xs text-text-muted">
            序话 Story — 让每个人都能创作属于自己的短片
          </p>
        </div>
      </main>
    </div>
  );
}
