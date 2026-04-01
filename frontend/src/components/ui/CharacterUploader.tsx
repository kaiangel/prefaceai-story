"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UserPlus, X, Loader2, ImagePlus } from "lucide-react";
import type { CharacterRef, StoryLength } from "@/types/create";
import { API_BASE, getStoredToken } from "@/lib/api";

const CHAR_RECOMMEND: Record<StoryLength, { min: number; max: number }> = {
  flash: { min: 2, max: 2 },
  short: { min: 3, max: 3 },
  medium: { min: 3, max: 4 },
  epic: { min: 4, max: 6 },
};

interface CharacterUploaderProps {
  characters: CharacterRef[];
  storyLength: StoryLength;
  onAdd: (character: CharacterRef) => void;
  onRemove: (id: string) => void;
}

export default function CharacterUploader({ characters, storyLength, onAdd, onRemove }: CharacterUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const maxChars = 5;
  const recommend = CHAR_RECOMMEND[storyLength] || CHAR_RECOMMEND.short;

  const handleFile = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    if (characters.length >= maxChars) return;

    setUploading(true);

    let name = "未命名角色";
    let analysisResult = null;

    try {
      const token = getStoredToken();
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(
        `${API_BASE}/utils/analyze-character`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        }
      );

      if (res.ok) {
        const data = await res.json();
        name = data.display_name || "未命名角色";
        analysisResult = data;
      }
    } catch {
      // Fallback: use default name
    }

    const newChar: CharacterRef = {
      id: `char_${Date.now()}`,
      name,
      uploadedImage: file,
      uploadedImageUrl: URL.createObjectURL(file),
      analysisResult,
      portraitUrl: null,
      fullbodyUrl: null,
    };
    onAdd(newChar);
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

  const remaining = recommend.min - characters.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-text-secondary">
          角色参考图 <span className="text-text-muted font-normal">（可选，最多{maxChars}个）</span>
        </label>
        <span className="text-xs text-text-muted">{characters.length}/{maxChars}</span>
      </div>

      {/* Recommendation hint */}
      {remaining > 0 && (
        <p className="text-xs text-text-muted">
          {storyLength === "flash" ? "快闪" : storyLength === "short" ? "短篇" : storyLength === "medium" ? "中篇" : "长篇"}推荐 {recommend.min} 个角色，建议再上传 {remaining} 个
        </p>
      )}
      {characters.length === 0 && (
        <p className="text-xs text-text-muted">未上传时，系统将根据故事自动补足角色</p>
      )}

      <div className="flex flex-wrap gap-3">
        <AnimatePresence mode="popLayout">
          {characters.map((char) => (
            <motion.div
              key={char.id}
              layout
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="relative w-20 h-20 rounded-lg overflow-hidden border border-white/10 group"
            >
              {char.uploadedImageUrl ? (
                <img src={char.uploadedImageUrl} alt={char.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-bg-secondary flex items-center justify-center">
                  <UserPlus className="w-6 h-6 text-text-muted" />
                </div>
              )}
              <button
                onClick={() => {
                  if (char.uploadedImageUrl) URL.revokeObjectURL(char.uploadedImageUrl);
                  onRemove(char.id);
                }}
                className="absolute top-0.5 right-0.5 w-5 h-5 bg-black/70 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3 text-white" />
              </button>
              <div className="absolute bottom-0 inset-x-0 bg-black/60 px-1 py-0.5 text-center">
                <span className="text-[10px] text-white truncate block">{char.name}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {characters.length < maxChars && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => fileRef.current?.click()}
            onDrop={onDrop}
            onDragOver={(e) => e.preventDefault()}
            disabled={uploading}
            className="w-20 h-20 rounded-lg border-2 border-dashed border-white/10 hover:border-brand-primary/50 flex flex-col items-center justify-center gap-1 transition-colors"
          >
            {uploading ? (
              <Loader2 className="w-5 h-5 text-brand-primary animate-spin" />
            ) : (
              <>
                <ImagePlus className="w-5 h-5 text-text-muted" />
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
