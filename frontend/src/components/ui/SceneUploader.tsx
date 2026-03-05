"use client";

import { useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ImagePlus, MapPin } from "lucide-react";
import type { SceneRef } from "@/types/create";

interface SceneUploaderProps {
  scenes: SceneRef[];
  onAdd: (scene: SceneRef) => void;
  onRemove: (id: string) => void;
}

export default function SceneUploader({ scenes, onAdd, onRemove }: SceneUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const maxScenes = 8;

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) return;
    if (scenes.length >= maxScenes) return;

    const newScene: SceneRef = {
      id: `scene_${Date.now()}`,
      name: `场景 ${scenes.length + 1}`,
      uploadedImage: file,
      uploadedImageUrl: URL.createObjectURL(file),
      interiorUrl: null,
      exteriorUrl: null,
    };
    onAdd(newScene);
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

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-text-secondary">
          场景参考图 <span className="text-text-muted font-normal">（可选，最多{maxScenes}个）</span>
        </label>
        <span className="text-xs text-text-muted">{scenes.length}/{maxScenes}</span>
      </div>

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
            className="w-24 h-16 rounded-lg border-2 border-dashed border-white/10 hover:border-brand-primary/50 flex flex-col items-center justify-center gap-1 transition-colors"
          >
            <ImagePlus className="w-4 h-4 text-text-muted" />
            <span className="text-[10px] text-text-muted">上传</span>
          </motion.button>
        )}
      </div>

      <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
    </div>
  );
}
