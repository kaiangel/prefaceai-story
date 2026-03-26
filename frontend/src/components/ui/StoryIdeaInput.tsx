"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { ImagePlus, Mic, MicOff, X, Lightbulb } from "lucide-react";
import { getStoredToken } from "@/lib/api";
import DocumentUploader from "./DocumentUploader";

const MOCK_VOICE_TEXT = "雨夜公交站，一个加班族和一个失恋女孩因为同一把伞产生交集的温暖故事";

const STORY_TEMPLATES = [
  "雨夜公交站，一个加班族和一个失恋女孩因为同一把伞产生交集",
  "深夜便利店，一个店员发现每天凌晨三点来买同一样东西的女人，背后隐藏着一个让人泪目的秘密",
  "外卖小哥送错了一份外卖，却意外改变了两个陌生人的命运",
  "爷爷留下的老照片里，藏着一段跨越60年的爱情故事",
  "一个社恐女孩被迫参加同学聚会，结果发现当年欺负她的人现在过得还不如她",
];

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
  const imageInputRef = useRef<HTMLInputElement>(null);
  const ocrTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const voiceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // OCR state
  const [ocrPreview, setOcrPreview] = useState<string | null>(null);
  const [ocrLoading, setOcrLoading] = useState(false);

  // Voice state
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);

  const clearTimers = useCallback(() => {
    if (ocrTimerRef.current) { clearTimeout(ocrTimerRef.current); ocrTimerRef.current = null; }
    if (voiceTimerRef.current) { clearTimeout(voiceTimerRef.current); voiceTimerRef.current = null; }
  }, []);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.max(120, el.scrollHeight)}px`;
    }
  }, [value]);

  // OCR handlers — real API call to POST /api/utils/ocr
  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setOcrPreview(url);
    setOcrLoading(true);
    e.target.value = "";

    try {
      const token = getStoredToken();
      const formData = new FormData();
      formData.append("file", file);

      const controller = new AbortController();
      ocrTimerRef.current = setTimeout(() => controller.abort(), 15000) as unknown as ReturnType<typeof setTimeout>;

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api"}/utils/ocr`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
          signal: controller.signal,
        }
      );

      if (!res.ok) throw new Error("OCR 识别失败");
      const data = await res.json();
      if (data.text) onChange(data.text);
    } catch {
      // Fallback: no text extracted, user can type manually
    } finally {
      setOcrLoading(false);
    }
  };

  const clearOcr = () => {
    if (ocrPreview) URL.revokeObjectURL(ocrPreview);
    setOcrPreview(null);
    setOcrLoading(false);
  };

  // Voice handlers
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      setVoiceLoading(true);
      voiceTimerRef.current = setTimeout(() => {
        onChange(MOCK_VOICE_TEXT);
        setVoiceLoading(false);
      }, 1000);
    } else {
      setIsRecording(true);
    }
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-text-secondary">
        故事创意 <span className="text-brand-primary">*</span>
      </label>

      {/* Textarea + action buttons */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={"写下你的故事创意...\n\n比如：雨夜公交站，一个加班族和一个失恋女孩因为同一把伞产生交集的温暖故事"}
          className={`w-full min-h-[120px] max-h-[300px] px-4 py-3 pr-20 bg-bg-secondary rounded-lg border text-text-primary placeholder:text-text-muted resize-none transition-colors focus:outline-none ${
            error
              ? "border-error focus:border-error"
              : "border-white/10 focus:border-brand-primary"
          }`}
        />

        {/* Action buttons — top right of textarea */}
        <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
          {/* Image OCR */}
          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
            className="p-1.5 rounded-md text-text-muted hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
            title="上传图片识别文字"
          >
            <ImagePlus className="w-4 h-4" />
          </button>
          <input
            ref={imageInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleImageSelect}
          />

          {/* Voice — hidden for MVP, code preserved */}
          {false && (
            <button
              type="button"
              onClick={toggleRecording}
              disabled={voiceLoading}
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                isRecording
                  ? "text-error bg-error/10 animate-pulse"
                  : voiceLoading
                    ? "text-text-muted opacity-50"
                    : "text-text-muted hover:text-brand-primary hover:bg-brand-primary/10"
              }`}
              title={isRecording ? "点击停止录音" : "语音输入"}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
          )}
        </div>

        {/* Status indicators */}
        {isRecording && (
          <div className="absolute bottom-14 left-4 flex items-center gap-2 text-xs text-error">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse" />
            正在录音...点击麦克风停止
          </div>
        )}
        {voiceLoading && (
          <div className="absolute bottom-14 left-4 text-xs text-brand-primary">
            正在转写...
          </div>
        )}

        {/* Bottom bar */}
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

      {/* OCR Preview */}
      {ocrPreview && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-bg-secondary border border-white/10">
          <img src={ocrPreview} alt="OCR预览" className="w-12 h-12 rounded object-cover flex-shrink-0" />
          <div className="flex-1 min-w-0">
            {ocrLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border-2 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
                <span className="text-xs text-brand-primary">正在识别图片中的文字...</span>
              </div>
            ) : (
              <span className="text-xs text-success">识别完成，已填入创意输入框</span>
            )}
          </div>
          <button onClick={clearOcr} className="text-text-muted hover:text-text-secondary cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Story Templates */}
      {!value.trim() && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-3.5 h-3.5 text-brand-primary" />
            <span className="text-xs text-text-muted">需要灵感？试试这些</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {STORY_TEMPLATES.map((tpl, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onChange(tpl)}
                className="text-xs px-3 py-1.5 rounded-full bg-bg-secondary border border-white/10 text-text-secondary hover:border-brand-primary/30 hover:text-brand-primary hover:bg-brand-primary/5 transition-all cursor-pointer text-left leading-relaxed"
              >
                {tpl.length > 30 ? tpl.slice(0, 30) + "..." : tpl}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
