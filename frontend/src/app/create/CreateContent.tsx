"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { mockOutline } from "@/lib/mock-data";
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

function StageA() {
  const { state, dispatch } = useCreate();
  const [ideaError, setIdeaError] = useState("");
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleSubmit = () => {
    if (!state.idea.trim()) {
      setIdeaError("请输入你的故事创意");
      return;
    }
    if (state.idea.length > 500) {
      setIdeaError("故事创意不能超过 500 字");
      return;
    }
    setIdeaError("");
    setLoading(true);
    // Mock: 模拟 AI 生成大纲，然后跳转到 Stage B
    timerRef.current = setTimeout(() => {
      dispatch({ type: "SET_OUTLINE", payload: mockOutline });
      dispatch({ type: "SET_STAGE", payload: "confirm" });
      setLoading(false);
      timerRef.current = null;
    }, 1500);
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
              onCustomStyleChange={(image, imageUrl, keywords) =>
                dispatch({ type: "SET_CUSTOM_STYLE", payload: { image, imageUrl, keywords } })
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
              onAdd={(c) => dispatch({ type: "ADD_CHARACTER", payload: c })}
              onRemove={(id) => dispatch({ type: "REMOVE_CHARACTER", payload: id })}
            />
            <SceneUploader
              scenes={state.scenes}
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
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 py-3.5 text-base"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  正在构思...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  生成故事
                </>
              )}
            </button>
            <p className="text-center text-text-muted text-xs mt-3">
              预计生成时间 3-5 分钟，取决于故事篇幅
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
