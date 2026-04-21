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

export async function apiFetch<T>(path: string, init: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
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
  token: string | null
): Promise<BgmInfo> {
  return apiFetch<BgmInfo>(`${BGM_BASE(projectId, chapter)}/bgm`, {}, token);
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
