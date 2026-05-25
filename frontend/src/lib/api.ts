"use client";

import type { BgmInfo, BgmRegenerateResponse, BgmVolumeResponse } from "@/types/create";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
const TOKEN_KEY = "preface_auth_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

// Options for apiFetch — extend this interface when adding new call-site options.
export interface ApiFetchOptions {
  // RISK-T18-G: Status codes that should NOT emit console.warn when they occur.
  // Use this for endpoints that legitimately return 4xx during early pipeline stages
  // (e.g. /chapters/1/story + /chapters/1/storyboard returning 404 before data exists).
  // The ApiError is still thrown (callers must .catch()); only the console.warn is suppressed
  // so that the client-log proxy does not record them as unexpected errors.
  silentStatuses?: number[];
}

// B37: Full-trace fetch wrapper — logs every request start, completion (with status+ms), and error.
// This is the single most critical logging point: ALL frontend API calls go through here.
export async function apiFetch<T>(path: string, init: RequestInit = {}, token?: string | null, options?: ApiFetchOptions): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const url = `${API_BASE}${path}`;
  const start = Date.now();

  // [API] Log #1 — request start
  // eslint-disable-next-line no-console
  console.log(`[API] ${method} ${path}`);

  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (networkErr) {
    const elapsed = Date.now() - start;
    // P3-2 (Wave 12): an in-flight fetch can stay pending while the browser tab is
    // backgrounded/suspended (e.g. laptop sleep). On resume the fetch rejects and the
    // wall-clock `elapsed` includes the entire suspension window — test26 logged bogus
    // "NETWORK_ERROR 5792945ms" (96 min). No real network request runs that long before
    // the platform times it out, so a huge elapsed is a tab-suspension signal, NOT a true
    // error. We flag it as such and downgrade to console.warn so it does not pollute
    // error-level monitoring.
    // Threshold: 2 min — well above any genuine request timeout, well below sleep gaps.
    const SUSPEND_ELAPSED_MS = 120_000;
    const wasHidden = typeof document !== "undefined" && document.visibilityState === "hidden";
    const likelySuspension = elapsed > SUSPEND_ELAPSED_MS || wasHidden;
    if (likelySuspension) {
      // [API] Log #2a — tab-suspension transient (not a genuine network failure)
      // eslint-disable-next-line no-console
      console.warn(
        `[API] ${method} ${path} NETWORK_ERROR (tab suspended, elapsed unreliable: ${elapsed}ms) — transient, will retry on resume`
      );
    } else {
      // [API] Log #2 — genuine network-level error (fetch threw, no response, plausible timing)
      // eslint-disable-next-line no-console
      console.error(`[API] ${method} ${path} NETWORK_ERROR ${elapsed}ms`, networkErr);
    }
    throw networkErr;
  }

  const elapsed = Date.now() - start;

  if (!response.ok) {
    // [API] Log #3 — HTTP error response
    // RISK-T18-G: suppress console.warn for status codes listed in options.silentStatuses.
    // These are by-design 4xx responses (e.g. 404 before chapter data exists) that callers
    // handle via .catch(). Skipping warn keeps the client-log proxy clean for real errors.
    const isSilent = options?.silentStatuses?.includes(response.status) ?? false;
    if (!isSilent) {
      // eslint-disable-next-line no-console
      console.warn(`[API] ${method} ${path} HTTP_ERROR status=${response.status} ${elapsed}ms`);
    }
    let detail = "请求失败";
    try {
      const payload = await response.json();
      if (Array.isArray(payload.detail)) {
        detail = payload.detail.map((e: Record<string, unknown>) => e.msg || e).join("; ");
      } else {
        detail = payload.detail || detail;
      }
    } catch {
      detail = await response.text() || detail;
    }
    throw new ApiError(detail, response.status);
  }

  // [API] Log #4 — success
  // eslint-disable-next-line no-console
  console.log(`[API] ${method} ${path} ${response.status} ${elapsed}ms`);

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

// ============ BGM API helpers (Wave 3, Step 6) ============

const BGM_BASE = (projectId: string, chapter: number) =>
  `/projects/${projectId}/chapters/${chapter}`;

export async function fetchBgmInfo(
  projectId: string,
  chapter: number,
  token: string | null,
  options?: ApiFetchOptions
): Promise<BgmInfo> {
  // RISK-T20-11.v2 (Wave 4): allow callers to pass silentStatuses so /outline phase
  // (BGM not yet generated → 404) doesn't pollute client.log with routine warns.
  return apiFetch<BgmInfo>(`${BGM_BASE(projectId, chapter)}/bgm`, {}, token, options);
}

export async function regenerateBgm(
  projectId: string,
  chapter: number,
  token: string | null
): Promise<BgmRegenerateResponse> {
  return apiFetch<BgmRegenerateResponse>(
    `${BGM_BASE(projectId, chapter)}/bgm/regenerate`,
    { method: "POST" },
    token
  );
}

export async function changeMetaBgm(
  projectId: string,
  chapter: number,
  token: string | null
): Promise<BgmRegenerateResponse> {
  return apiFetch<BgmRegenerateResponse>(
    `${BGM_BASE(projectId, chapter)}/bgm/change-meta`,
    { method: "POST" },
    token
  );
}

export async function patchBgmVolume(
  projectId: string,
  chapter: number,
  volume: number,   // 0-1
  token: string | null
): Promise<BgmVolumeResponse> {
  return apiFetch<BgmVolumeResponse>(
    `${BGM_BASE(projectId, chapter)}/bgm/volume`,
    {
      method: "PATCH",
      body: JSON.stringify({ volume }),
    },
    token
  );
}
