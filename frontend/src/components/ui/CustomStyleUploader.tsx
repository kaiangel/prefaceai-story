"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Palette, X, Loader2, Sparkles } from "lucide-react";
import { API_BASE, getStoredToken } from "@/lib/api";

interface StyleAnalysisResult {
  style_display_name: string;
  mandatory_keywords: string[];
  forbidden_keywords: string[];
  style_description: string;
  quality_keywords: string[];
  display_tags: string[];
}

interface CustomStyleUploaderProps {
  image: File | null;
  imageUrl: string | null;
  keywords: string[];
  onUpload: (image: File | null, imageUrl: string | null, keywords: string[], analysis?: Record<string, unknown> | null) => void;
}

export default function CustomStyleUploader({ image, imageUrl, keywords, onUpload }: CustomStyleUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith("image/")) return;

    const url = URL.createObjectURL(file);
    // 立即显示图片预览 + loading（分析中）
    onUpload(file, url, [], null);
    setAnalyzing(true);

    try {
      const token = getStoredToken();
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(
        `${API_BASE}/utils/analyze-style`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        }
      );

      if (!res.ok) throw new Error("风格分析失败");
      const result: StyleAnalysisResult = await res.json();
      onUpload(file, url, result.display_tags || [], result as unknown as Record<string, unknown>);
    } catch {
      onUpload(file, url, ["自定义风格"], null);
    } finally {
      setAnalyzing(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
    e.target.value = "";
  };

  const clear = () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    onUpload(null, null, [], null);
  };

  if (image && imageUrl) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-3 bg-bg-secondary rounded-lg border border-brand-primary/30"
      >
        <div className="flex items-start gap-3">
          <img src={imageUrl} alt="自定义风格" className="w-16 h-16 rounded-md object-cover shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-text-primary flex items-center gap-1">
                <Palette className="w-3.5 h-3.5 text-brand-primary" />
                自定义风格
              </span>
              <button onClick={clear} className="text-text-muted hover:text-text-primary transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            {analyzing ? (
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <Loader2 className="w-3 h-3 animate-spin" />
                AI 正在分析风格特征...
              </div>
            ) : (
              <div className="flex flex-wrap gap-1">
                {keywords.map((kw, i) => (
                  <span key={i} className="px-1.5 py-0.5 text-[10px] bg-brand-primary/10 text-brand-primary rounded">
                    {kw}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <button
      onClick={() => fileRef.current?.click()}
      className="w-full flex items-center justify-center gap-2 py-3 rounded-lg border-2 border-dashed border-white/10 hover:border-brand-primary/30 text-text-muted hover:text-text-secondary transition-colors"
    >
      <Sparkles className="w-4 h-4" />
      <span className="text-sm">上传参考图，AI 提取风格</span>
      <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
    </button>
  );
}
