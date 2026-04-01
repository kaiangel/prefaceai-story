"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ImagePlus, MapPin, Loader2 } from "lucide-react";
import type { SceneRef, StoryLength } from "@/types/create";
import { API_BASE, getStoredToken } from "@/lib/api";

const SCENE_RECOMMEND: Record<StoryLength, { min: number; max: number }> = {
  flash: { min: 2, max: 3 },
  short: { min: 3, max: 4 },
  medium: { min: 4, max: 6 },
  epic: { min: 5, max: 8 },
};

interface SceneUploaderProps {
  scenes: SceneRef[];
  storyLength: StoryLength;
  onAdd: (scene: SceneRef) => void;
  onRemove: (id: string) => void;
}

export default function SceneUploader({ scenes, storyLength, onAdd, onRemove }: SceneUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const maxScenes = 8;
  const recommend = SCENE_RECOMMEND[storyLength] || SCENE_RECOMMEND.short;

  const handleFile = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    if (scenes.length >= maxScenes) return;

    setUploading(true);

    let name = `场景 ${scenes.length + 1}`;
    let analysisResult = null;

    try {
      const token = getStoredToken();
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(
        `${API_BASE}/utils/analyze-scene`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        }
      );

      if (res.ok) {
        const data = await res.json();
        name = data.display_name || name;
        analysisResult = data;
      }
    } catch {
      // Fallback: use default name
    }

    const newScene: SceneRef = {
      id: `scene_${Date.now()}`,
      name,
      uploadedImage: file,
      uploadedImageUrl: URL.createObjectURL(file),
      analysisResult,
      interiorUrl: null,
      exteriorUrl: null,
    };
    onAdd(newScene);
    setUploading(false);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const remaining = recommend.min - scenes.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-text-secondary">
          场景参考图 <span className="text-text-muted font-normal">（可选，最多{maxScenes}个）</span>
        </label>
        <span className="text-xs text-text-muted">{scenes.length}/{maxScenes}</span>
      </div>

      {/* Recommendation hint */}
      {remaining > 0 && (
        <p className="text-xs text-text-muted">
          {storyLength === "flash" ? "快闪" : storyLength === "short" ? "短篇" : storyLength === "medium" ? "中篇" : "长篇"}推荐 {recommend.min}-{recommend.max} 个场景，建议再上传 {remaining} 个
        </p>
      )}
      {scenes.length === 0 && (
        <p className="text-xs text-text-muted">未上传时，系统将根据故事自动生成场景</p>
      )}

      <div className="flex flex-wrap gap-3">
        <AnimatePresence mode="popLayout">
          {scenes.map((scene) => (
            <motion.div
              key={scene.id}
              layout
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="relative w-24 h-16 rounded-lg overflow-hidden border border-white/10 group"
            >
              {scene.uploadedImageUrl ? (
                <img src={scene.uploadedImageUrl} alt={scene.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-bg-secondary flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-text-muted" />
                </div>
              )}
              <button
                onClick={() => {
                  if (scene.uploadedImageUrl) URL.revokeObjectURL(scene.uploadedImageUrl);
                  onRemove(scene.id);
                }}
                className="absolute top-0.5 right-0.5 w-5 h-5 bg-black/70 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3 text-white" />
              </button>
              <div className="absolute bottom-0 inset-x-0 bg-black/60 px-1 py-0.5 text-center">
                <span className="text-[10px] text-white truncate block">{scene.name}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {scenes.length < maxScenes && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => fileRef.current?.click()}
            onDrop={onDrop}
            onDragOver={(e) => e.preventDefault()}
            disabled={uploading}
            className="w-24 h-16 rounded-lg border-2 border-dashed border-white/10 hover:border-brand-primary/50 flex flex-col items-center justify-center gap-1 transition-colors"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 text-brand-primary animate-spin" />
            ) : (
              <>
                <ImagePlus className="w-4 h-4 text-text-muted" />
                <span className="text-[10px] text-text-muted">上传</span>
              </>
            )}
          </motion.button>
        )}
      </div>

      <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
    </div>
  );
}
