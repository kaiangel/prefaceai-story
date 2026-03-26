"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, AlertCircle } from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { mockOutline } from "@/lib/mock-data";
import type { StoryOutline, StoryLength } from "@/types/create";
import CreateHeader from "@/components/layout/CreateHeader";
import StoryIdeaInput from "@/components/ui/StoryIdeaInput";
import LengthSelector from "@/components/ui/LengthSelector";
import StyleSelector from "@/components/ui/StyleSelector";
import AspectRatioSelector from "@/components/ui/AspectRatioSelector";
import CharacterUploader from "@/components/ui/CharacterUploader";
import SceneUploader from "@/components/ui/SceneUploader";
import StageB from "@/components/create/StageB";
import StageC from "@/components/create/StageC";
import StageD from "@/components/create/StageD";
import StageE from "@/components/create/StageE";

// Length → API parameters mapping
const LENGTH_PARAMS: Record<StoryLength, { duration: number; characters: number }> = {
  flash: { duration: 1, characters: 2 },
  short: { duration: 3, characters: 3 },
  medium: { duration: 6, characters: 3 },
  epic: { duration: 6, characters: 4 },
};

function StageA() {
  const { state, dispatch } = useCreate();
  const { isLoggedIn } = useAuth();
  const [ideaError, setIdeaError] = useState("");
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleSubmit = async () => {
    if (!state.idea.trim() && !state.documentText?.trim()) {
      setIdeaError("请输入故事创意或上传故事文档");
      return;
    }
    if (state.idea.length > 500) {
      setIdeaError("故事创意不能超过 500 字");
      return;
    }
    setIdeaError("");
    setApiError("");
    setLoading(true);

    const token = getStoredToken();

    // If not logged in or no token, use mock data
    if (!isLoggedIn || !token) {
      timerRef.current = setTimeout(() => {
        dispatch({ type: "SET_OUTLINE", payload: mockOutline });
        dispatch({ type: "SET_STAGE", payload: "confirm" });
        setLoading(false);
      }, 1500);
      return;
    }

    try {
      const params = LENGTH_PARAMS[state.length] || LENGTH_PARAMS.short;

      // Step 1: Create project
      const project = await apiFetch<{ project_id: string }>(
        "/projects/",
        {
          method: "POST",
          body: JSON.stringify({
            original_idea: state.idea.trim(),
            style_preset: state.stylePreset || "illustration",
            total_chapters: 1,
            chapter_duration_minutes: params.duration,
            character_count: params.characters,
            language: "zh-CN",
            aspect_ratio: state.aspectRatio || "2:3",
            document_text: state.documentText || null,
            custom_style_analysis: state.customStyleAnalysis || null,
            character_refs_analysis: state.characters
              .filter(c => c.analysisResult)
              .map(c => c.analysisResult),
            scene_refs_analysis: state.scenes
              .filter(s => s.analysisResult)
              .map(s => s.analysisResult),
          }),
        },
        token
      );

      // Step 2: Generate outline (synchronous, 10-30s)
      const outline = await apiFetch<StoryOutline>(
        `/projects/${project.project_id}/generate-outline`,
        { method: "POST" },
        token
      );

      dispatch({ type: "SET_OUTLINE", payload: outline });
      dispatch({ type: "SET_STAGE", payload: "confirm" });
    } catch (err) {
      const message = err instanceof Error ? err.message : "生成失败，请稍后重试";
      setApiError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleIdeaChange = (value: string) => {
    dispatch({ type: "SET_IDEA", payload: value });
    if (ideaError) setIdeaError("");
  };

  return (
    <main className="container-lg py-8 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">开始创作</h1>
          <p className="text-text-tertiary text-sm">
            输入创意，AI 帮你生成完整条漫
          </p>
        </div>

        {/* Form */}
        <div className="space-y-8">
          {/* Story Idea + Document Upload */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <StoryIdeaInput
              value={state.idea}
              onChange={handleIdeaChange}
              error={ideaError}
              documentFile={state.documentFile}
              onDocumentUpload={(file, text) =>
                dispatch({ type: "SET_DOCUMENT", payload: { file, text } })
              }
            />
          </motion.div>

          {/* Length Selector */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <LengthSelector
              value={state.length}
              onChange={(v) => dispatch({ type: "SET_LENGTH", payload: v })}
              continuationMode={state.continuationMode}
              onContinuationModeChange={(m) =>
                dispatch({ type: "SET_CONTINUATION_MODE", payload: m })
              }
            />
          </motion.div>

          {/* Aspect Ratio */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <AspectRatioSelector
              value={state.aspectRatio}
              onChange={(v) => dispatch({ type: "SET_ASPECT_RATIO", payload: v })}
            />
          </motion.div>

          {/* Style Selector */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <StyleSelector
              value={state.stylePreset}
              onChange={(v) => dispatch({ type: "SET_STYLE_PRESET", payload: v })}
              customStyleImage={state.customStyleImage}
              customStyleImageUrl={state.customStyleImageUrl}
              customStyleKeywords={state.customStyleKeywords}
              onCustomStyleChange={(image, imageUrl, keywords, analysis) =>
                dispatch({ type: "SET_CUSTOM_STYLE", payload: { image, imageUrl, keywords, analysis } })
              }
            />
          </motion.div>

          {/* Character & Scene Uploaders */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-6"
          >
            <CharacterUploader
              characters={state.characters}
              storyLength={state.length}
              onAdd={(c) => dispatch({ type: "ADD_CHARACTER", payload: c })}
              onRemove={(id) => dispatch({ type: "REMOVE_CHARACTER", payload: id })}
            />
            <SceneUploader
              scenes={state.scenes}
              storyLength={state.length}
              onAdd={(s) => dispatch({ type: "ADD_SCENE", payload: s })}
              onRemove={(id) => dispatch({ type: "REMOVE_SCENE", payload: id })}
            />
          </motion.div>

          {/* Submit */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="pt-2"
          >
            {/* API Error */}
            {apiError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-error/10 border border-error/20 mb-3">
                <AlertCircle className="w-4 h-4 text-error flex-shrink-0" />
                <span className="text-sm text-error flex-1">{apiError}</span>
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 py-3.5 text-base"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  AI 正在构思故事大纲...
                </>
              ) : apiError ? (
                <>
                  <Sparkles className="w-4 h-4" />
                  重试
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  生成故事
                </>
              )}
            </button>
            <p className="text-center text-text-muted text-xs mt-3">
              {loading ? "大纲生成中，约需 10-30 秒..." : "AI 将根据你的创意生成完整故事大纲"}
            </p>
          </motion.div>
        </div>
      </motion.div>
    </main>
  );
}

export default function CreateContent() {
  const { state } = useCreate();

  const renderStage = () => {
    switch (state.currentStage) {
      case "input":
        return <StageA />;
      case "confirm":
        return <StageB />;
      case "generate":
        return <StageC />;
      case "preview":
        return <StageD />;
      case "deliver":
        return <StageE />;
      default:
        return <StageA />;
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <CreateHeader />
      {renderStage()}
    </div>
  );
}
