"use client";

import { createContext, useContext, useState, useCallback, useEffect, useRef, type ReactNode } from "react";
import type { User, RegisterForm, StoryCard } from "@/types/create";
import { apiFetch, ApiError, getStoredToken, setStoredToken } from "@/lib/api";
import { toAbsoluteUrl } from "@/lib/url";

interface AuthContextValue {
  user: User | null;
  isLoggedIn: boolean;
  stories: StoryCard[];
  login: (email: string, password: string) => Promise<boolean>;
  register: (form: RegisterForm) => Promise<boolean>;
  logout: () => void;
  deleteStory: (storyId: string) => Promise<void>;
  updateUser: (updates: Partial<User>) => Promise<boolean>;
  refreshStories: () => Promise<void>;
  loadingUser: boolean;
}

interface ApiUser {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  plan: string;
  credits: number;
  created_at: string;
}

interface AuthResponse {
  success: boolean;
  token: string;
  user: ApiUser;
}

interface ApiProject {
  id: string;
  title: string;
  original_idea: string;
  style_preset: string;
  created_at: string;
  updated_at: string;
  cover_image_url: string | null;
  shot_count: number;
  mood: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function mapUser(user: ApiUser): User {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    avatarUrl: user.avatar_url,
    plan: user.plan,
    credits: user.credits,
    createdAt: user.created_at,
  };
}

function inferLength(idea: string): StoryCard["length"] {
  const size = idea.length;
  if (size < 80) return "flash";
  if (size < 250) return "short";
  if (size < 600) return "medium";
  return "epic";
}

function mapProject(project: ApiProject): StoryCard {
  // Infer status from shot_count: shot_count > 0 means the pipeline has completed
  // (shots were generated). Otherwise treat as draft / in-progress.
  const inferredStatus: StoryCard["status"] = project.shot_count > 0 ? "complete" : "draft";
  return {
    id: project.id,
    title: project.title || "未命名故事",
    coverImageUrl: toAbsoluteUrl(project.cover_image_url) ?? "/brand/logo-48.png",
    style: project.style_preset,
    length: inferLength(project.original_idea || project.title),
    shotCount: project.shot_count,
    mood: project.mood,
    status: inferredStatus,
    createdAt: project.created_at,   // ISO 8601 with Z from backend; new Date() parses correctly as UTC
    updatedAt: project.updated_at,
    canContinue: true,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [stories, setStories] = useState<StoryCard[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  // BUG-T13-AUTH-FALSE-LOGOUT-ON-500: track whether the token has been definitively
  // proven invalid (got a 401). If only 5xx/network errors so far, presume token still
  // valid — guarded pages should NOT redirect to /login on 5xx cascades.
  const [tokenInvalid, setTokenInvalid] = useState(false);

  const refreshStories = useCallback(async (authToken?: string | null) => {
    const currentToken = authToken ?? token ?? getStoredToken();
    if (!currentToken) {
      setStories([]);
      return;
    }
    const projects = await apiFetch<ApiProject[]>("/projects/", {}, currentToken);
    setStories(projects.map(mapProject));
  }, [token]);

  const hydrateSession = useCallback(async (authToken: string) => {
    // [Auth] Log #1 — session hydration start (token present from localStorage)
    // eslint-disable-next-line no-console
    console.log("[Auth] hydrateSession: fetching /auth/me to restore session");
    const me = await apiFetch<ApiUser>("/auth/me", {}, authToken);
    setUser(mapUser(me));
    // [Auth] Log #2 — session hydration: user loaded
    // eslint-disable-next-line no-console
    console.log("[Auth] hydrateSession: user loaded id=", me.id, "email=", me.email, "plan=", me.plan);
    // refreshStories 失败不阻塞登录（项目列表为空但用户仍登录）
    try {
      await refreshStories(authToken);
      // [Auth] Log #3 — stories refreshed successfully
      // eslint-disable-next-line no-console
      console.log("[Auth] hydrateSession: stories refreshed OK");
    } catch (e) {
      // 静默: 项目列表稍后重试
      // eslint-disable-next-line no-console
      console.warn("[Auth] hydrateSession: refreshStories failed (non-fatal):", e instanceof Error ? e.message : e);
    }
  }, [refreshStories]);

  // BUG-T13-AUTH-FALSE-LOGOUT-ON-500 fix:
  // When /auth/me returns 5xx / network error / timeout, we previously set loadingUser=false
  // with user=null → isLoggedIn=false → all guarded pages redirected to /login.
  // The token was actually still valid; backend was just temporarily unavailable
  // (e.g. MySQL pool exhaustion during peak load).
  //
  // New behavior:
  //   - Token absent → loadingUser=false (anonymous, no redirect needed)
  //   - Token present + /auth/me === 200 → loadingUser=false, user set, isLoggedIn=true
  //   - Token present + /auth/me === 401 → loadingUser=false, clear token, isLoggedIn=false
  //   - Token present + /auth/me 5xx/network/timeout → KEEP loadingUser=true and retry with backoff.
  //     Guarded pages stay in loading state instead of bouncing to /login.
  const sessionRetryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionRetryAttemptRef = useRef(0);

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      // [Auth] Log #4 — no stored token: anonymous session
      // eslint-disable-next-line no-console
      console.log("[Auth] useEffect: no stored token → anonymous session");
      setLoadingUser(false);
      return;
    }

    // [Auth] Log #5 — stored token found: attempting session restore
    // eslint-disable-next-line no-console
    console.log("[Auth] useEffect: stored token found → hydrateSession");
    setToken(stored);

    let cancelled = false;

    const attemptHydrate = async (isRetry: boolean) => {
      if (cancelled) return;
      try {
        await hydrateSession(stored);
        if (cancelled) return;
        sessionRetryAttemptRef.current = 0;
        setTokenInvalid(false);
        setLoadingUser(false);
      } catch (err) {
        if (cancelled) return;
        // 401 → token genuinely invalid, force re-login
        if (err instanceof ApiError && err.status === 401) {
          // [Auth] Log #6 — 401 → clear token, force re-login
          // eslint-disable-next-line no-console
          console.warn("[Auth] hydrateSession: 401 → clearing token, user must re-login");
          setStoredToken(null);
          setToken(null);
          setUser(null);
          setStories([]);
          setTokenInvalid(true);
          setLoadingUser(false);
          return;
        }
        // 5xx / network / timeout → keep token, retry with backoff.
        // BUG-T13-AUTH-FALSE-LOGOUT-ON-500 fix: set loadingUser=false so guarded pages render
        // (they'll see isLoggedIn=true via tokenInvalid=false despite user=null), but keep retrying
        // in background so user data fills in once backend recovers.
        sessionRetryAttemptRef.current++;
        const attempt = sessionRetryAttemptRef.current;
        const backoffMs = Math.min(2000 * Math.pow(2, attempt - 1), 30000); // 2s, 4s, 8s, 16s, 30s cap
        // eslint-disable-next-line no-console
        console.warn(
          "[Auth] hydrateSession: non-401 error (attempt",
          attempt,
          "), retry in",
          backoffMs,
          "ms — token preserved, isLoggedIn=true (token still presumed valid):",
          err instanceof Error ? err.message : err
        );
        // First failure: still set loadingUser=false so the app doesn't show a blank/loading
        // screen forever during outage. Subsequent retries don't change loadingUser.
        if (!isRetry) {
          setLoadingUser(false);
        }
        sessionRetryTimerRef.current = setTimeout(() => {
          attemptHydrate(true);
        }, backoffMs);
      }
    };

    attemptHydrate(false);

    return () => {
      cancelled = true;
      if (sessionRetryTimerRef.current) {
        clearTimeout(sessionRetryTimerRef.current);
        sessionRetryTimerRef.current = null;
      }
    };
  }, [hydrateSession]);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    // [Auth] Log #7 — login attempt
    // eslint-disable-next-line no-console
    console.log("[Auth] login: attempt for email=", email);
    try {
      const response = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setStoredToken(response.token);
      setToken(response.token);
      setTokenInvalid(false);
      setUser(mapUser(response.user));
      await refreshStories(response.token);
      // [Auth] Log #8 — login success
      // eslint-disable-next-line no-console
      console.log("[Auth] login: SUCCESS user id=", response.user.id, "plan=", response.user.plan);
      return true;
    } catch (e) {
      // [Auth] Log #9 — login failed
      // eslint-disable-next-line no-console
      console.warn("[Auth] login: FAILED:", e instanceof Error ? e.message : e);
      return false;
    }
  }, [refreshStories]);

  const register = useCallback(async (form: RegisterForm): Promise<boolean> => {
    // [Auth] Log #10 — register attempt
    // eslint-disable-next-line no-console
    console.log("[Auth] register: attempt for email=", form.email);
    try {
      const response = await apiFetch<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          invite_code: form.inviteCode,
        }),
      });
      setStoredToken(response.token);
      setToken(response.token);
      setTokenInvalid(false);
      setUser(mapUser(response.user));
      setStories([]);
      // [Auth] Log #11 — register success
      // eslint-disable-next-line no-console
      console.log("[Auth] register: SUCCESS user id=", response.user.id);
      return true;
    } catch (e) {
      // [Auth] Log #12 — register failed
      // eslint-disable-next-line no-console
      console.warn("[Auth] register: FAILED:", e instanceof Error ? e.message : e);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    // [Auth] Log #13 — logout
    // eslint-disable-next-line no-console
    console.log("[Auth] logout: clearing session");
    setStoredToken(null);
    setToken(null);
    setUser(null);
    setStories([]);
    setTokenInvalid(false); // Reset on logout so next login starts clean
  }, []);

  const deleteStory = useCallback(async (storyId: string) => {
    const currentToken = token ?? getStoredToken();
    if (!currentToken) return;
    await apiFetch(`/projects/${storyId}`, { method: "DELETE" }, currentToken);
    setStories((prev) => prev.filter((s) => s.id !== storyId));
  }, [token]);

  const updateUser = useCallback(async (updates: Partial<User>) => {
    const currentToken = token ?? getStoredToken();
    if (!currentToken || !user) return false;

    const payload = {
      name: (updates.name || user?.name || "").trim(),
      avatar_url: updates.avatarUrl ?? user?.avatarUrl ?? null,
    };

    try {
      const response = await apiFetch<ApiUser>("/auth/me", {
        method: "PUT",
        body: JSON.stringify(payload),
      }, currentToken);
      setUser(mapUser(response));
      return true;
    } catch {
      return false;
    }
  }, [token, user]);

  // BUG-T13-AUTH-FALSE-LOGOUT-ON-500 fix:
  //   - !!user (success path: /auth/me returned 200) → logged in
  //   - !!token && !tokenInvalid (token still in localStorage and not 401'd) → logged in
  //     even when /auth/me is currently failing with 5xx (presume token still valid).
  //   - tokenInvalid=true (got a 401) or no token → logged out.
  const isLoggedIn = !!user || (!!token && !tokenInvalid);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn,
        stories,
        login,
        register,
        logout,
        deleteStory,
        updateUser,
        refreshStories,
        loadingUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
