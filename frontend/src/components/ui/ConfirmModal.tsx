"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "确定",
  cancelLabel = "取消",
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!open) return null;

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 z-50"
        onClick={onCancel}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          className="bg-bg-secondary border border-white/10 rounded-xl p-6 w-full max-w-sm"
          onClick={(e) => e.stopPropagation()}
        >
          {danger && (
            <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-error" />
            </div>
          )}
          <h3 className="text-lg font-semibold text-text-primary text-center mb-2">{title}</h3>
          <p className="text-text-tertiary text-sm text-center mb-6">{message}</p>
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-lg border border-white/10 text-text-secondary text-sm hover:bg-white/5 transition-colors cursor-pointer"
            >
              {cancelLabel}
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 py-2.5 rounded-lg text-white text-sm font-medium cursor-pointer ${
                danger ? "bg-error hover:bg-error/90" : "bg-brand-primary hover:bg-brand-primary/90"
              } transition-colors`}
            >
              {confirmLabel}
            </button>
          </div>
        </motion.div>
      </div>
    </>
  );
}
