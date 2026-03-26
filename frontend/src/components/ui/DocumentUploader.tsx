"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { FileText, X, Upload } from "lucide-react";
import { getStoredToken } from "@/lib/api";

interface DocumentUploaderProps {
  file: File | null;
  onUpload: (file: File | null, text: string) => void;
}

const ACCEPTED_EXTENSIONS = ".txt,.md,.pdf";

export default function DocumentUploader({ file, onUpload }: DocumentUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);

  const extractText = async (f: File): Promise<string> => {
    if (f.type === "application/pdf") {
      // PDF: call backend parse-document API
      try {
        const token = getStoredToken();
        const formData = new FormData();
        formData.append("file", f);
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api"}/utils/parse-document`,
          {
            method: "POST",
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData,
          }
        );
        if (!res.ok) throw new Error("PDF 解析失败");
        const data = await res.json();
        return data.text || "";
      } catch {
        return `[PDF 文档: ${f.name}] 解析失败，请尝试复制文字手动粘贴`;
      }
    }
    return await f.text();
  };

  const handleFile = async (f: File) => {
    setLoading(true);
    const text = await extractText(f);
    onUpload(f, text);
    setLoading(false);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
    e.target.value = "";
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const clear = () => onUpload(null, "");

  if (file) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-2 px-3 py-2 bg-bg-secondary rounded-lg border border-white/10"
      >
        <FileText className="w-4 h-4 text-brand-primary shrink-0" />
        <span className="text-sm text-text-secondary truncate flex-1">{file.name}</span>
        <button onClick={clear} className="text-text-muted hover:text-text-primary transition-colors">
          <X className="w-4 h-4" />
        </button>
      </motion.div>
    );
  }

  return (
    <button
      onClick={() => fileRef.current?.click()}
      onDrop={onDrop}
      onDragOver={(e) => e.preventDefault()}
      disabled={loading}
      className="flex items-center gap-2 px-3 py-2 text-sm text-text-muted hover:text-text-secondary border border-dashed border-white/10 hover:border-white/20 rounded-lg transition-colors"
    >
      <Upload className="w-4 h-4" />
      {loading ? "读取中..." : "或上传故事文档 (txt/md/PDF)"}
      <input ref={fileRef} type="file" accept={ACCEPTED_EXTENSIONS} className="hidden" onChange={onFileChange} />
    </button>
  );
}
