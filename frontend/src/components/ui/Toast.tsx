"use client";

import { useState, useCallback, createContext, useContext, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((type: ToastType, message: string) => {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2 max-w-sm">
        <AnimatePresence>
          {toasts.map((t) => (
            <ToastMessage key={t.id} item={t} onDismiss={dismiss} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

const ICON_MAP = {
  success: <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />,
  error: <XCircle className="w-4 h-4 text-error flex-shrink-0" />,
  info: <Info className="w-4 h-4 text-info flex-shrink-0" />,
};

const BG_MAP = {
  success: "bg-success/10 border-success/20",
  error: "bg-error/10 border-error/20",
  info: "bg-info/10 border-info/20",
};

function ToastMessage({ item, onDismiss }: { item: ToastItem; onDismiss: (id: number) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.95 }}
      className={`flex items-center gap-2.5 px-4 py-3 rounded-xl border backdrop-blur-md shadow-lg ${BG_MAP[item.type]}`}
    >
      {ICON_MAP[item.type]}
      <span className="text-sm text-text-primary flex-1">{item.message}</span>
      <button onClick={() => onDismiss(item.id)} className="text-text-muted hover:text-text-secondary transition-colors">
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}
