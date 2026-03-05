"use client";

import { useRef, useEffect } from "react";
import DocumentUploader from "./DocumentUploader";

interface StoryIdeaInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  documentFile: File | null;
  onDocumentUpload: (file: File | null, text: string) => void;
}

export default function StoryIdeaInput({
  value,
  onChange,
  error,
  documentFile,
  onDocumentUpload,
}: StoryIdeaInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.max(120, el.scrollHeight)}px`;
    }
  }, [value]);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">
        故事创意 <span className="text-brand-primary">*</span>
      </label>
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={"写下你的故事创意...\n\n比如：雨夜公交站，一个加班族和一个失恋女孩因为同一把伞产生交集的温暖故事"}
          className={`w-full min-h-[120px] max-h-[300px] px-4 py-3 bg-bg-secondary rounded-lg border text-text-primary placeholder:text-text-muted resize-none transition-colors focus:outline-none ${
            error
              ? "border-error focus:border-error"
              : "border-white/10 focus:border-brand-primary"
          }`}
        />
        <div className="flex items-center justify-between mt-1.5">
          {error ? (
            <span className="text-xs text-error">{error}</span>
          ) : (
            <DocumentUploader file={documentFile} onUpload={onDocumentUpload} />
          )}
          <span className={`text-xs ${value.length > 500 ? "text-warning" : "text-text-muted"}`}>
            {value.length}/500
          </span>
        </div>
      </div>
    </div>
  );
}
