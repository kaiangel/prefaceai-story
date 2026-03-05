"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { mockGenerationProgress } from "@/lib/mock-data";

export default function StageC() {
  const { state, dispatch } = useCreate();
  const cancelRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    dispatch({ type: "START_GENERATION" });

    const cancel = mockGenerationProgress(
      (progress, message) => {
        dispatch({ type: "UPDATE_GENERATION_PROGRESS", payload: { progress, message } });
      },
      (shots) => {
        dispatch({ type: "GENERATION_COMPLETE", payload: shots });
        dispatch({ type: "SET_STAGE", payload: "preview" });
      }
    );
    cancelRef.current = cancel;

    return () => {
      cancel();
    };
  }, [dispatch]);

  const isError = state.generationStatus === "error";

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-lg mx-auto text-center"
      >
        {/* Icon */}
        <motion.div
          className="mb-8"
          animate={isError ? {} : { scale: [1, 1.05, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          {isError ? (
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto" />
          ) : (
            <Loader2 className="w-16 h-16 text-brand-primary mx-auto animate-spin" />
          )}
        </motion.div>

        {/* Title */}
        <h1 className="text-2xl font-bold mb-2">
          {isError ? "生成遇到问题" : "正在创作你的故事"}
        </h1>
        <p className="text-text-tertiary text-sm mb-8">
          {isError
            ? state.generationMessage
            : "AI 正在全力创作，请耐心等待"}
        </p>

        {/* Progress Bar */}
        {!isError && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-muted">进度</span>
              <span className="text-xs text-text-muted">{state.generationProgress}%</span>
            </div>
            <div className="w-full h-2 bg-bg-secondary rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-brand-primary to-purple-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${state.generationProgress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </div>
        )}

        {/* Current Step */}
        {!isError && state.generationMessage && (
          <motion.p
            key={state.generationMessage}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-brand-primary mb-6"
          >
            {state.generationMessage}
          </motion.p>
        )}

        {/* Generation Log */}
        {state.generationLog.length > 0 && (
          <div className="bg-bg-secondary rounded-xl p-4 border border-white/5 text-left max-h-48 overflow-y-auto">
            <div className="space-y-2">
              {state.generationLog.map((entry, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0" />
                  <span className="text-text-tertiary">{entry.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error: Retry */}
        {isError && (
          <button
            onClick={() => {
              dispatch({ type: "SET_STAGE", payload: "confirm" });
            }}
            className="btn-primary mt-6 px-8"
          >
            返回重试
          </button>
        )}
      </motion.div>
    </main>
  );
}
