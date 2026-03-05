"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User as UserIcon, LayoutDashboard, LogOut, ChevronDown } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) return null;

  const initials = user.name
    .split(/[\s_-]/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors"
      >
        {/* Avatar */}
        {user.avatarUrl ? (
          <img src={user.avatarUrl} alt={user.name} className="w-7 h-7 rounded-full object-cover" />
        ) : (
          <div className="w-7 h-7 rounded-full bg-brand-primary/20 flex items-center justify-center text-[11px] font-medium text-brand-primary">
            {initials}
          </div>
        )}
        <span className="text-sm text-text-secondary hidden sm:block max-w-[100px] truncate">
          {user.name}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-text-muted transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -5, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -5, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 z-50 bg-bg-tertiary border border-white/10 rounded-xl shadow-xl py-2 min-w-[200px]"
            >
              {/* User info */}
              <div className="px-3 py-2 border-b border-white/5">
                <p className="text-sm font-medium text-text-primary truncate">{user.name}</p>
                <p className="text-xs text-text-muted truncate">{user.email}</p>
              </div>

              {/* Links */}
              <div className="py-1">
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:bg-white/5 transition-colors"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  我的工作台
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:bg-white/5 transition-colors"
                >
                  <UserIcon className="w-4 h-4" />
                  个人设置
                </Link>
              </div>

              {/* Logout */}
              <div className="border-t border-white/5 pt-1">
                <button
                  onClick={() => { logout(); setOpen(false); }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-error hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  退出登录
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
