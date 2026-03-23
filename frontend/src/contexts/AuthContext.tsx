"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import type { User, RegisterForm, StoryCard } from "@/types/create";
import { apiFetch, getStoredToken, setStoredToken } from "@/lib/api";

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
    coverImageUrl: "/brand/logo-48.png",
    style: project.style_preset,
    length: inferLength(project.original_idea || project.title),
    shotCount: 0,
    createdAt: project.created_at,
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
    await refreshStories(authToken);
  }, [refreshStories]);

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      setLoadingUser(false);
      return;
    }

    setToken(stored);
    hydrateSession(stored)
      .catch(() => {
        setStoredToken(null);
        setToken(null);
        setUser(null);
        setStories([]);
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
