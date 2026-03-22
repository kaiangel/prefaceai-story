"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { User, RegisterForm, StoryCard } from "@/types/create";
import { mockUserStories } from "@/lib/mock-data";

interface AuthContextValue {
  user: User | null;
  isLoggedIn: boolean;
  stories: StoryCard[];
  login: (email: string, password: string) => Promise<boolean>;
  register: (form: RegisterForm) => Promise<boolean>;
  logout: () => void;
  deleteStory: (storyId: string) => void;
  updateUser: (updates: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [stories, setStories] = useState<StoryCard[]>([]);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const login = useCallback(async (email: string, _password: string): Promise<boolean> => {
    // Mock login
    await new Promise((r) => setTimeout(r, 800));
    setUser({
      id: "user_001",
      email,
      name: email.split("@")[0],
      avatarUrl: null,
      createdAt: new Date().toISOString(),
    });
    setStories(mockUserStories);
    return true;
  }, []);

  const register = useCallback(async (form: RegisterForm): Promise<boolean> => {
    // Mock register — validate invite code
    await new Promise((r) => setTimeout(r, 1000));
    // Mock: any non-empty invite code is accepted
    if (!form.inviteCode.trim()) return false;
    setUser({
      id: `user_${Date.now()}`,
      email: form.email,
      name: form.email.split("@")[0],
      avatarUrl: null,
      createdAt: new Date().toISOString(),
    });
    setStories([]); // New user, no stories
    return true;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setStories([]);
  }, []);

  const deleteStory = useCallback((storyId: string) => {
    setStories((prev) => prev.filter((s) => s.id !== storyId));
  }, []);

  const updateUser = useCallback((updates: Partial<User>) => {
    setUser((prev) => prev ? { ...prev, ...updates } : prev);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoggedIn: !!user, stories, login, register, logout, deleteStory, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
