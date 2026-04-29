/**
 * URL utilities — shared across StageD, BgmPlayer, StoryDetailContent, etc.
 *
 * P0-1 (TASK-T6-FIXBATCH): StageD was rendering /static/... paths directly,
 * which the browser resolves to http://localhost:3000/static/... (frontend port)
 * instead of http://127.0.0.1:8000/static/... (backend port). This helper
 * converts any /static/... path into an absolute backend URL.
 */

import { API_BASE } from "@/lib/api";

// Backend server base: strip trailing /api from API_BASE
// e.g. "http://127.0.0.1:8000/api" → "http://127.0.0.1:8000"
export const SERVER_BASE = API_BASE.replace(/\/api\/?$/, "");

/**
 * Convert a relative /static/... URL to an absolute backend URL.
 * - Already absolute (http/https) URLs are returned unchanged.
 * - null / undefined → null
 * - Strips surrounding quotes if the backend returns them as `"/static/..."` (P3-4 fix)
 */
export function toAbsoluteUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  // Strip surrounding double-quotes (backend sometimes returns `"url"` with quotes)
  const stripped = url.replace(/^"|"$/g, "");
  if (!stripped) return null;
  if (stripped.startsWith("http://") || stripped.startsWith("https://")) return stripped;
  if (stripped.startsWith("/")) return `${SERVER_BASE}${stripped}`;
  return stripped;
}
