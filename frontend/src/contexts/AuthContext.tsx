"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
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
  return {
    id: project.id,
    title: project.title || "未命名故事",
    coverImageUrl: toAbsoluteUrl(project.cover_image_url) ?? "/brand/logo-48.png",
    style: project.style_preset,
    length: inferLength(project.original_idea || project.title),
    shotCount: project.shot_count,
    mood: project.mood,
    createdAt: project.created_at,   // ISO 8601 with Z from backend; new Date() parses correctly as UTC
    updatedAt: project.updated_at,
    status: "draft",
    canContinue: true,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [stories, setStories] = useState<StoryCard[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

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
    const me = await apiFetch<ApiUser>("/auth/me", {}, authToken);
    setUser(mapUser(me));
    // refreshStories 失败不阻塞登录（项目列表为空但用户仍登录）
    try {
      await refreshStories(authToken);
    } catch {
      // 静默: 项目列表稍后重试
    }
  }, [refreshStories]);

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      setLoadingUser(false);
      return;
    }

    setToken(stored);
    hydrateSession(stored)
      .catch((err) => {
        // 只有 401（token 真正失效）才清 token
        if (err instanceof ApiError && err.status === 401) {
          setStoredToken(null);
          setToken(null);
          setUser(null);
          setStories([]);
        }
        // 其他错误（500/超时/网络）保留 token，下次刷新重试
      })
      .finally(() => setLoadingUser(false));
  }, [hydrateSession]);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setStoredToken(response.token);
      setToken(response.token);
      setUser(mapUser(response.user));
      await refreshStories(response.token);
      return true;
    } catch {
      return false;
    }
  }, [refreshStories]);

  const register = useCallback(async (form: RegisterForm): Promise<boolean> => {
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
      setUser(mapUser(response.user));
      setStories([]);
      return true;
    } catch {
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
    setStories([]);
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
      name: (updates.name || user.name).trim(),
      avatar_url: updates.avatarUrl ?? user.avatarUrl ?? null,
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

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn: !!user,
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
